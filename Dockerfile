# Começa com uma imagem base do Python 3.11
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos para dentro do contêiner
COPY requirements.txt ./requirements.txt

# Instala as bibliotecas Python listadas no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os outros arquivos do seu projeto (código, dados, imagens)
COPY . .

# Expõe a porta que o Streamlit usa
EXPOSE 8501

# Define o comando para iniciar o aplicativo quando o contêiner rodar
CMD ["streamlit", "run", "Dashboard.py"]