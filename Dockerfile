FROM python:3.10
WORKDIR /app
ADD . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["echo", "Vultra is ready to run."]
