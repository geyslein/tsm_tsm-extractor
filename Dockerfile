FROM python:3-alpine

#RUN apk add py3-numpy --no-cache

# Create a group and user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup --uid 1000
# Tell docker that all future commands should run as the appuser user
USER appuser

WORKDIR /home/appuser/app/src

COPY src .

RUN pip install -r requirements.txt
ENTRYPOINT ["python", "main.py"]
