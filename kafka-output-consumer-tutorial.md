# Deploying and Testing the Output Consumer Application on Kubernetes

This tutorial shows how to deploy and test the output consumer that reads telemetry from Kafka and sends it to Elasticsearch.

## 🎯 What We're Deploying

- **Python application** that consumes telemetry messages from Kafka
- **Elasticsearch integration** for storing and indexing telemetry data
- **Real-time data pipeline** from Kafka to Elasticsearch
- **Simple, lightweight consumer** with minimal overhead

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or similar)
- Kafka already deployed on Kubernetes
- Elasticsearch deployed on Kubernetes
- Application Docker image available: `eduardorfarias/output-consumer-app:latest`

## 🚀 Deployment Steps

### Step 1: Deploy the Application

The deployment YAML is already configured in `/output-consumer/output-consumer-deployment.yaml`:

```bash
# Deploy the application
kubectl apply -f output-consumer/output-consumer-deployment.yaml

# Check deployment status
kubectl get pods
```

You should see something like:

```
NAME                                  READY   STATUS    RESTARTS   AGE
output-consumer-app-7d9b5c4f8-xq2wz   1/1     Running   0          30s
```

### Step 2: Verify Application Startup

Check the logs to ensure the application connected to both Kafka and Elasticsearch:

```bash
# Check logs from the pod
kubectl logs output-consumer-app-7d9b5c4f8-xq2wz

# Look for these success messages:
# "Connecting to Kafka: kafka:9092"
# "Connecting to Elasticsearch: elasticsearch:9200"
# "Consuming from topic: jogo-da-vida-output"
```

## 🧪 Testing the Application

### Send Test Telemetry via OpenMP App

First, make sure your OpenMP app is running and send it a message:

```bash
# Send test message to trigger telemetry generation
echo '{"powmin":3,"powmax":5}' | kubectl exec -i kafka-consumer -- kafka-console-producer --bootstrap-server kafka:9092 --topic jogo-da-vida
```

### Monitor the Consumer Processing

```bash
# Watch the consumer logs in real-time
kubectl logs -f output-consumer-app-7d9b5c4f8-xq2wz

# You should see:
# Received: {'tam': 8, 'init': 2.9e-06, 'comp': 0.1483381, 'fim': 6e-06, 'tot': 0.1483469}
# Sent to Elasticsearch: {'tam': 8, 'init': 2.9e-06, 'comp': 0.1483381, 'fim': 6e-06, 'tot': 0.1483469, 'timestamp': '2024-01-15T10:30:45.123456'}
```

### Verify Data in Elasticsearch

```bash
# Check if data is being indexed in Elasticsearch
kubectl exec -it elasticsearch-pod -- curl -X GET "localhost:9200/jogo-da-vida-telemetry/_search?pretty"

# You should see documents like:
# {
#   "_source": {
#     "tam": 8,
#     "init": 2.9e-06,
#     "comp": 0.1483381,
#     "fim": 6e-06,
#     "tot": 0.1483469,
#     "timestamp": "2024-01-15T10:30:45.123456"
#   }
# }
```

## 🔍 Understanding the Data Flow

### Complete Pipeline

```
OpenMP App → Kafka (jogo-da-vida-output) → [Output Consumer] → Elasticsearch → Kibana
```

### Input from Kafka (jogo-da-vida-output topic)

```json
{
  "tam": 8,
  "init": 2.9e-6,
  "comp": 0.1483381,
  "fim": 6e-6,
  "tot": 0.1483469
}
```

### Output to Elasticsearch (jogo-da-vida-telemetry index)

```json
{
  "tam": 8,
  "init": 2.9e-6,
  "comp": 0.1483381,
  "fim": 6e-6,
  "tot": 0.1483469,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 🔧 Quick Troubleshooting

### If Pod Doesn't Start

```bash
kubectl describe pod <pod-name>
# Check for resource constraints or image pull issues
```

### If No Data Reaches Elasticsearch

```bash
# Check Kafka connectivity
kubectl logs <pod-name> | grep "Connecting to Kafka"

# Check Elasticsearch connectivity
kubectl logs <pod-name> | grep "Connecting to Elasticsearch"

# Verify the topic has messages
kubectl exec -it kafka-consumer -- kafka-console-consumer --bootstrap-server kafka:9092 --topic jogo-da-vida-output --from-beginning
```

### Scale the Consumer (if needed)

```bash
# Scale to multiple replicas for higher throughput
kubectl scale deployment output-consumer-app --replicas=2
```

## 🎉 Success Indicators

✅ **Deployment**: Pod running successfully  
✅ **Kafka Connection**: "Connecting to Kafka" message in logs  
✅ **Elasticsearch Connection**: "Connecting to Elasticsearch" message in logs  
✅ **Message Processing**: "Received:" and "Sent to Elasticsearch:" in logs  
✅ **Data in Elasticsearch**: Documents visible in Elasticsearch index

Your output consumer is now successfully deployed and streaming telemetry data from Kafka to Elasticsearch! 🚀

## 🎨 Next Steps: Kibana Dashboards

Once data is flowing into Elasticsearch, you can create visualizations in Kibana:

1. **Create Index Pattern**: `jogo-da-vida-telemetry*`
2. **Set Time Field**: `timestamp`
3. **Create Visualizations**:
   - Line chart: `tot` (total execution time) over time
   - Bar chart: Average execution time by `tam` (matrix size)
   - Metrics: Min/Max/Average of `comp` (computation time)
