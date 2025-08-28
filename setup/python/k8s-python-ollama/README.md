# k8s-python-ollama Project

This project sets up a Kubernetes environment for deploying a FastAPI application and managing Ollama containers. Below are the details for setting up and running the project.

## Prerequisites

- Ubuntu distribution in WSL on Windows 11
- Docker installed and running
- Kubernetes installed (e.g., using Minikube or kind)
- kubectl command-line tool installed
- Python 3.x installed

## Project Structure

```
k8s-python-ollama
├── src
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── k8s
│   ├── namespace.yaml
│   ├── fastapi
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── ollama
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── persistent-volume.yaml
│   └── ingress.yaml
├── scripts
│   ├── setup-k8s.sh
│   ├── deploy.sh
│   └── cleanup.sh
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd k8s-python-ollama
   ```

2. **Install dependencies**:
   Navigate to the `src` directory and install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. **Set up Kubernetes**:
   Run the setup script to install necessary tools and configure the Kubernetes environment:
   ```
   ./scripts/setup-k8s.sh
   ```

4. **Deploy the applications**:
   Use the deploy script to deploy the FastAPI and Ollama applications to the Kubernetes cluster:
   ```
   ./scripts/deploy.sh
   ```

5. **Access the applications**:
   If you have set up Ingress, you can access the applications via the configured hostnames. Otherwise, you can use the service IPs to access them.

## Cleanup Instructions

To remove the deployed resources from the Kubernetes cluster, run:
```
./scripts/cleanup.sh
```

## Additional Information

- The FastAPI application is defined in `src/app.py` and can be modified as needed.
- The Dockerfile in the `src` directory is used to build the Docker image for the FastAPI application.
- Kubernetes manifests are located in the `k8s` directory, organized by application.

For any issues or contributions, please refer to the project's GitHub page.