https://github.com/HKUDS/LightRAG

```
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG
# create a Python virtual enviroment if neccesary
# Install in editable mode with API support
pip install -e ".[api]"
cp env.example .env
lightrag-server
```

```
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG
cp env.example .env
# modify LLM and Embedding settings in .env
docker compose up
```