FROM python
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["echo", "hello! this is my image!"]
