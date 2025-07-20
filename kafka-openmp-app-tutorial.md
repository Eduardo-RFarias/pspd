# Deploying a Python OpenMP Application with Kafka on Kubernetes

This tutorial shows how to deploy a Python application that uses OpenMP (C code) and connects to Kafka for message processing, all running on Kubernetes with maximum simplicity.

## 🎯 What We're Building

- **Python application** that consumes JSON messages from Kafka
- **OpenMP C code execution** for parallel processing
- **Kafka producer** that sends telemetry back to Kafka
- **2 replicas** running in Kubernetes for high availability
- **Simple auto-created topics** for ease of use

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or similar)
- Kafka already deployed on Kubernetes
- Docker Hub account
- Docker installed locally

## 🚀 Step-by-Step Implementation

### Step 1: Prepare the Application

Our Python application (`main.py`) does the following:

1. **Consumes** messages from Kafka topic `jogo-da-vida`
2. **Extracts** `powmin` and `powmax` from JSON
3. **Executes** OpenMP C code with those parameters
4. **Parses** the output logs
5. **Sends** telemetry back to `jogo-da-vida-output` topic

**Key Configuration (Environment Variables):**

```python
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.environ.get("TOPIC_IN", "jogo-da-vida")
TOPIC_OUT = os.environ.get("TOPIC_OUT", "jogo-da-vida-output")
GROUP_ID = os.environ.get("GROUP_ID", "jogo-da-vida-group")
```

**Important Kafka Consumer Settings:**

```python
consumer = KafkaConsumer(
    TOPIC_IN,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset="earliest",
    enable_auto_commit=True,           # ✅ Automatic offset management
    group_id=GROUP_ID,                 # ✅ Enables load balancing between replicas
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)
```

### Step 2: Optimize the Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:bookworm-slim

RUN apt-get update && apt-get install -y gcc libomp-dev make

WORKDIR /app

COPY jogodavida_openmp.c Makefile /app/
RUN make jogodavida_openmp

COPY pyproject.toml uv.lock /app/
RUN uv sync

COPY main.py /app/

ENV OMP_NUM_THREADS=4                  # ⚡ 4 threads for parallel processing
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
```

### Step 3: Build and Push Docker Image

```bash
# Navigate to app directory
cd openmp-app

# Build the image
docker build -t yourusername/openmp-kafka-app:latest .

# Push to Docker Hub
docker push yourusername/openmp-kafka-app:latest
```

### Step 4: Create Kubernetes Deployment

Create `openmp-app-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openmp-kafka-app
  labels:
    app: openmp-kafka-app
spec:
  replicas: 2 # 🔄 2 replicas for high availability
  selector:
    matchLabels:
      app: openmp-kafka-app
  template:
    metadata:
      labels:
        app: openmp-kafka-app
    spec:
      containers:
        - name: openmp-kafka-app
          image: yourusername/openmp-kafka-app:latest
          env:
            - name: KAFKA_BROKER
              value: "kafka:9092" # 🔗 Points to Kafka service
            - name: TOPIC_IN
              value: "jogo-da-vida"
            - name: TOPIC_OUT
              value: "jogo-da-vida-output"
            - name: GROUP_ID
              value: "jogo-da-vida-group" # 👥 Consumer group for load balancing
            - name: OMP_NUM_THREADS
              value: "4"
          resources:
            requests:
              cpu: "1" # 💡 Realistic CPU request
              memory: "512Mi"
            limits:
              cpu: "2" # 🚀 Allow burst to 2 CPUs
              memory: "1Gi"
          imagePullPolicy: Always
```

### Step 5: Deploy to Kubernetes

```bash
# Apply the deployment
kubectl apply -f openmp-app-deployment.yaml

# Check deployment status
kubectl get pods

# View logs (should be empty until messages arrive)
kubectl logs deployment/openmp-kafka-app
```

## 🔍 How It Works

### **Load Balancing Magic** 🎯

- **Consumer Group**: All replicas join the same `jogo-da-vida-group`
- **Automatic Distribution**: Kafka automatically distributes messages between the 2 replicas
- **No Duplicate Processing**: Each message is processed by only one replica

### **Resource Allocation** ⚡

- **CPU Request**: 1 CPU guaranteed per pod
- **CPU Limit**: Can burst up to 2 CPUs when available
- **OpenMP Threads**: 4 threads for parallel processing
- **Memory**: 512Mi-1Gi per pod

### **Topic Auto-Creation** 🚀

- **Simplicity**: Topics are created automatically when first used
- **No Manual Setup**: Just start sending messages!
- **Development-Friendly**: Perfect for testing and development

## 📝 Testing the Deployment

### Send a Test Message

```bash
# Connect to Kafka pod
kubectl exec -it kafka-0 -- /bin/sh

# Send test message
kafka-console-producer --bootstrap-server localhost:9092 --topic jogo-da-vida
{"powmin": 10, "powmax": 20}
```

### Check Processing

```bash
# View application logs
kubectl logs -f deployment/openmp-kafka-app

# Check output topic
kubectl exec -it kafka-0 -- kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic jogo-da-vida-output \
  --from-beginning
```

## 🎉 Expected Results

1. **Input**: JSON with `powmin` and `powmax`
2. **Processing**: OpenMP C code executes in parallel
3. **Output**: Telemetry JSON with timing data:
   ```json
   {
     "tam": 1024,
     "init": 0.001,
     "comp": 0.25,
     "fim": 0.002,
     "tot": 0.253
   }
   ```

## 🔧 Troubleshooting

### Pod Not Starting

- **Check Resources**: Reduce CPU requests if cluster has limited resources
- **View Events**: `kubectl describe pod <pod-name>`
- **Check Logs**: `kubectl logs <pod-name>`

### No Message Processing

- **Verify Kafka Connection**: Check `KAFKA_BROKER` environment variable
- **Topic Names**: Ensure input topic has messages
- **Consumer Group**: Check if other consumers are in the same group

### Performance Issues

- **CPU Allocation**: Increase CPU limits for better OpenMP performance
- **Thread Count**: Adjust `OMP_NUM_THREADS` based on available resources
- **Memory**: Monitor memory usage and adjust limits

## 🏆 Key Success Factors

1. **✅ Consumer Group Configuration**: Enables automatic load balancing
2. **✅ Realistic Resource Requests**: Prevents scheduling issues
3. **✅ Environment Variable Configuration**: Maximum flexibility
4. **✅ Auto-commit Enabled**: Simplifies offset management
5. **✅ Auto-topic Creation**: Reduces setup complexity

This deployment provides a robust, scalable solution for processing Kafka messages with OpenMP parallel computation in Kubernetes! 🚀
