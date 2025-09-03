import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any
import json
import uuid
from datetime import datetime

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
    AutoModelForSequenceClassification, DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TuningServiceImpl(mcp_service_pb2_grpc.TuningServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("TuningService")
        self.setup_tuning_environment()
        self.active_jobs = {}
    
    def setup_tuning_environment(self):
        """Initialize tuning environment"""
        # Check for GPU availability
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Default model configurations
        self.model_configs = {
            'gpt2': {
                'model_name': 'gpt2',
                'task_type': TaskType.CAUSAL_LM
            },
            'distilbert': {
                'model_name': 'distilbert-base-uncased',
                'task_type': TaskType.SEQ_CLS
            },
            'llama2-7b': {
                'model_name': 'meta-llama/Llama-2-7b-hf',
                'task_type': TaskType.CAUSAL_LM
            }
        }
        
        # LoRA configurations
        self.lora_configs = {
            'causal_lm': LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=8,
                lora_alpha=32,
                lora_dropout=0.1
            ),
            'seq_cls': LoraConfig(
                task_type=TaskType.SEQ_CLS,
                inference_mode=False,
                r=8,
                lora_alpha=32,
                lora_dropout=0.1
            )
        }
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Tuning Service is healthy"
        )
    
    async def TuneModel(self, request, context):
        """Fine-tune a model with provided training data"""
        try:
            training_data = list(request.training_data)
            model_type = request.model_type or 'gpt2'
            tuning_config = dict(request.tuning_config)
            
            job_id = str(uuid.uuid4())
            logger.info(f"Starting tuning job {job_id} for model {model_type}")
            
            # Start tuning as a background task
            task = asyncio.create_task(
                self._tune_model_async(job_id, training_data, model_type, tuning_config)
            )
            self.active_jobs[job_id] = {
                'task': task,
                'status': 'running',
                'start_time': datetime.now(),
                'model_type': model_type
            }
            
            return mcp_service_pb2.TuningResponse(
                model_id=job_id,
                success=True,
                message=f"Tuning job {job_id} started successfully"
            )
            
        except Exception as e:
            logger.error(f"Error starting tuning job: {str(e)}")
            return mcp_service_pb2.TuningResponse(
                model_id="",
                success=False,
                message=f"Error starting tuning job: {str(e)}"
            )
    
    async def _tune_model_async(self, job_id, training_data, model_type, config):
        """Asynchronously tune a model"""
        try:
            logger.info(f"Processing {len(training_data)} training examples for job {job_id}")
            
            # Prepare training data
            dataset = self._prepare_dataset(training_data, config)
            
            # Setup model and tokenizer
            model_config = self.model_configs.get(model_type, self.model_configs['gpt2'])
            model_name = model_config['model_name']
            task_type = model_config['task_type']
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model
            if task_type == TaskType.CAUSAL_LM:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            else:
                num_labels = len(set([doc.metadata.get('label', '0') for doc in training_data]))
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=num_labels
                )
            
            # Apply LoRA
            use_lora = config.get('use_lora', 'true').lower() == 'true'
            if use_lora:
                lora_config_key = 'causal_lm' if task_type == TaskType.CAUSAL_LM else 'seq_cls'
                lora_config = self.lora_configs[lora_config_key]
                model = get_peft_model(model, lora_config)
            
            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    padding='max_length',
                    max_length=int(config.get('max_length', 512))
                )
            
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            # Setup training arguments
            output_dir = f"./models/{job_id}"
            training_args = TrainingArguments(
                output_dir=output_dir,
                overwrite_output_dir=True,
                num_train_epochs=int(config.get('num_epochs', 3)),
                per_device_train_batch_size=int(config.get('batch_size', 4)),
                learning_rate=float(config.get('learning_rate', 5e-5)),
                warmup_steps=int(config.get('warmup_steps', 100)),
                logging_steps=int(config.get('logging_steps', 10)),
                save_steps=int(config.get('save_steps', 500)),
                evaluation_strategy="steps" if 'eval_steps' in config else "no",
                eval_steps=int(config.get('eval_steps', 500)) if 'eval_steps' in config else None,
                save_total_limit=2,
                prediction_loss_only=True,
                remove_unused_columns=False,
                dataloader_pin_memory=False
            )
            
            # Data collator
            if task_type == TaskType.CAUSAL_LM:
                data_collator = DataCollatorForLanguageModeling(
                    tokenizer=tokenizer,
                    mlm=False
                )
            else:
                data_collator = None
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator
            )
            
            # Train model
            logger.info(f"Starting training for job {job_id}")
            await asyncio.to_thread(trainer.train)
            
            # Save model
            await asyncio.to_thread(trainer.save_model)
            
            # Update job status
            self.active_jobs[job_id]['status'] = 'completed'
            self.active_jobs[job_id]['output_dir'] = output_dir
            
            logger.info(f"Training completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error in tuning job {job_id}: {str(e)}")
            self.active_jobs[job_id]['status'] = 'failed'
            self.active_jobs[job_id]['error'] = str(e)
    
    def _prepare_dataset(self, training_data, config):
        """Prepare dataset from training documents"""
        dataset_format = config.get('format', 'text')
        
        if dataset_format == 'text':
            # Simple text dataset
            texts = [doc.content for doc in training_data]
            dataset = Dataset.from_dict({'text': texts})
            
        elif dataset_format == 'classification':
            # Classification dataset
            texts = [doc.content for doc in training_data]
            labels = [int(doc.metadata.get('label', 0)) for doc in training_data]
            dataset = Dataset.from_dict({'text': texts, 'labels': labels})
            
        elif dataset_format == 'instruction':
            # Instruction-following dataset
            texts = []
            for doc in training_data:
                instruction = doc.metadata.get('instruction', '')
                response = doc.content
                text = f"### Instruction:\n{instruction}\n\n### Response:\n{response}"
                texts.append(text)
            dataset = Dataset.from_dict({'text': texts})
            
        else:
            # Default to text format
            texts = [doc.content for doc in training_data]
            dataset = Dataset.from_dict({'text': texts})
        
        return dataset
    
    def get_job_status(self, job_id):
        """Get the status of a tuning job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                'status': job['status'],
                'start_time': job['start_time'].isoformat(),
                'model_type': job['model_type'],
                'output_dir': job.get('output_dir'),
                'error': job.get('error')
            }
        return None

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_TuningServiceServicer_to_server(
        TuningServiceImpl(), server
    )
    
    listen_addr = '[::]:50058'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Tuning Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
