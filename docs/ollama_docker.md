docker run -d --name ollama -p 11434:11434 -v D:\ollama-models:/root/.ollama ollama/ollama


docker save -o ollama_image.tar ollama/ollama

docker exec ollama ollama run llama3.1:8b

docker exec ollama ollama delete

docker network create ollama-net
docker run -d --name ollama --network ollama-net -p 11434:11434 ollama/ollama
docker run -d --name dify --network ollama-net -p 5000:5000 dify/dify