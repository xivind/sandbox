# Docker file based on this tutorial https://python.plainenglish.io/turn-your-python-script-into-a-real-program-with-docker-c200e15d5265

# First stage
FROM python:3.9 AS builder
COPY send-strava-requirements.txt requirements.txt

# Install dependencies to the local user directory
RUN pip3 install --user -r requirements.txt

# Second unnamed stage
FROM python:3.9-slim
WORKDIR /code

# Copy only files needed for the application to be run within the container and the source files
COPY --from=builder /root/.local /root/.local
COPY send_strava.py .

# Update PATH
ENV PATH=/root/.local:$PATH

# Start program and remember to include the -u flag to have stdout logged
# Pass arguments for the script when creating the container, see sh-file
# Note the use of ENTRYPOINT instead of CMD. If not logging to console will not work
ENTRYPOINT ["python3", "-u"]
