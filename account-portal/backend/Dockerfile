FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y     curl     unzip     && rm -rf /var/lib/apt/lists/*

# Install AWS Session Manager Plugin
RUN curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"     && dpkg -i session-manager-plugin.deb     && rm session-manager-plugin.deb

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Ansible AWS collection
RUN ansible-galaxy collection install amazon.aws

COPY . .

CMD ["python", "app.py"]
