# Deploying Spark on Kubernetes Tutorial

This tutorial shows how to deploy Apache Spark on Kubernetes to process Conway's Game of Life simulations with Kafka integration.

## 🎯 What We're Deploying

- **Apache Spark** application that consumes JSON messages from Kafka
- **PySpark distributed processing** for Conway's Game of Life simulation
- **Kafka integration** that sends telemetry back to Kafka
- **Compatible with existing pipeline** (OpenMP + Output Consumer + ELK Stack)

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or similar)
- Kafka already deployed on Kubernetes
- Docker for building the application image

## 🚀 Deployment Steps

### Step 1: Build and Push Docker Image

```bash
# Navigate to the spark-app directory
cd spark-app

# Build the Docker image
docker build -t eduardorfarias/spark-game-of-life:latest .

# Push to Docker Hub (make sure you're logged in)
docker push eduardorfarias/spark-game-of-life:latest
```

### Step 2: Deploy RBAC Configuration

Spark needs permissions to create executor pods in Kubernetes:

```bash
# Apply RBAC configuration for Spark
kubectl apply -f spark-app/spark-rbac.yaml

# Verify service account was created
kubectl get serviceaccount spark
```

### Step 3: Deploy the Spark Application

```bash
# Deploy the Spark application
kubectl apply -f spark-app/spark-app-deployment.yaml

# Check deployment status
kubectl get pods -l app=spark-game-of-life-app
```

You should see something like:

```
NAME                                   READY   STATUS    RESTARTS   AGE
spark-game-of-life-app-7d8c5f9b-xyz   1/1     Running   0          30s
```

### Step 4: Verify Application Startup

```bash
# Check logs to ensure the application connected to Kafka
kubectl logs -l app=spark-game-of-life-app

# Look for these success messages:
# "Starting Spark Game of Life application"
# "Consumidor conectado ao broker 'kafka:9092' e inscrito no tópico 'jogo-da-vida-spark'"
```

## 🧪 Testing the Spark Application

### Send a Test Message

```bash
# Send test message to trigger Spark processing
echo '{"powmin":3,"powmax":5}' | kubectl exec -i kafka-consumer -- kafka-console-producer --bootstrap-server kafka:9092 --topic jogo-da-vida-spark
```

### Monitor Processing

```bash
# Watch the Spark application logs in real-time
kubectl logs -l app=spark-game-of-life-app -f

# You should see messages like:
# "[*] Mensagem recebida: {'powmin': 3, 'powmax': 5}"
# "Starting simulation for board size 2^3 = 8"
# "[*] Telemetria enviada: {'game_id': '...', 'step': 1, 'total_steps': 3, 'board_size': 8, ...}"
```

### Check Output in Kafka

```bash
# Monitor the output topic to see telemetry data
kubectl exec -i kafka-consumer -- kafka-console-consumer --bootstrap-server kafka:9092 --topic jogo-da-vida-output --from-beginning

# You should see JSON messages like:
# {"game_id": "uuid", "step": 1, "total_steps": 3, "board_size": 8, "start_time": 1700000000, "end_time": 1700000002, "impl": "spark"}
```

## 🔧 Configuration

The Spark application uses the same environment variables as the OpenMP app:

- **KAFKA_BROKER**: Kafka broker address (default: `kafka:9092`)
- **TOPIC_IN**: Input topic for simulation requests (default: `jogo-da-vida-spark`)
- **TOPIC_OUT**: Output topic for telemetry data (default: `jogo-da-vida-output`)
- **GROUP_ID**: Kafka consumer group ID (default: `spark-jogo-da-vida-group`)

## 🔍 Key Features

1. **Environment Variable Configuration**: Uses the same pattern as OpenMP app
2. **Automatic Kubernetes Detection**: Spark automatically configures for distributed execution in K8s
3. **Compatible Output Schema**: Sends the exact same telemetry format as OpenMP app
4. **Proper RBAC**: Service account with necessary permissions for Spark executors
5. **Resource Management**: CPU and memory limits for the driver pod

## 🎭 Comparison with OpenMP App

| Feature          | OpenMP App            | Spark App                  |
| ---------------- | --------------------- | -------------------------- |
| Input Topic      | `jogo-da-vida`        | `jogo-da-vida-spark`       |
| Output Topic     | `jogo-da-vida-output` | `jogo-da-vida-output`      |
| Message Format   | JSON                  | JSON (identical)           |
| Telemetry Schema | ✅                    | ✅ (identical)             |
| Implementation   | `"impl": "openmp"`    | `"impl": "spark"`          |
| Processing       | Single-node parallel  | Distributed across cluster |

## 🔧 Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app=spark-game-of-life-app
kubectl describe pod <spark-pod-name>
```

### View Detailed Logs

```bash
kubectl logs <spark-pod-name> -f
```

### Check Spark UI (if needed)

```bash
# Port forward to access Spark UI
kubectl port-forward <spark-pod-name> 4040:4040
# Then open http://localhost:4040
```

### Common Issues

1. **RBAC Permissions**: Make sure `spark-rbac.yaml` is applied
2. **Image Pull**: Ensure the Docker image is pushed and accessible
3. **Kafka Connection**: Verify Kafka is running and accessible at `kafka:9092`
4. **Resource Limits**: Adjust CPU/memory if needed for your cluster

## 🔗 Integration with Existing Pipeline

This Spark application integrates seamlessly with your existing pipeline:

1. **Input**: Receives messages from `jogo-da-vida-spark` topic
2. **Processing**: Uses distributed Spark to process Game of Life simulations
3. **Output**: Sends telemetry to `jogo-da-vida-output` topic
4. **Consumption**: Output Consumer picks up telemetry and sends to Elasticsearch
5. **Visualization**: Kibana dashboards show results from both OpenMP and Spark implementations

Now you have both OpenMP and Spark implementations running in parallel, processing different input topics but producing compatible output!
