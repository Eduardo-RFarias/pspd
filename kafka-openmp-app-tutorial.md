# Deploying and Testing the OpenMP Kafka Application on Kubernetes

This tutorial shows how to deploy and test a Python OpenMP application that processes Kafka messages on Kubernetes.

## 🎯 What We're Deploying

- **Python application** that consumes JSON messages from Kafka
- **OpenMP C code execution** for parallel processing
- **Kafka producer** that sends telemetry back to Kafka
- **2 replicas** running in Kubernetes for high availability

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or similar)
- Kafka already deployed on Kubernetes
- Application Docker image available: `eduardorfarias/openmp-kafka-app:latest`

## 🚀 Deployment Steps

### Step 1: Deploy the Application

The deployment YAML is already configured in `/openmp-app/openmp-app-deployment.yaml`:

```bash
# Deploy the application
kubectl apply -f openmp-app/openmp-app-deployment.yaml

# Scale to 2 replicas for load balancing
kubectl scale deployment openmp-kafka-app --replicas=2

# Check deployment status
kubectl get pods
```

You should see something like:

```
NAME                               READY   STATUS    RESTARTS   AGE
openmp-kafka-app-66d9f5487-9q4fh   1/1     Running   0          30s
openmp-kafka-app-66d9f5487-mszg9   1/1     Running   0          30s
```

### Step 2: Verify Application Startup

Check the logs to ensure the application connected to Kafka:

```bash
# Check logs from one of the pods
kubectl logs openmp-kafka-app-66d9f5487-9q4fh

# Look for these success messages:
# "Consumidor conectado ao broker 'kafka:9092' e inscrito no tópico 'jogo-da-vida'"
```

## 🧪 Testing the Application

### Send a Test Message

```bash
# Send test message with powmin=3, powmax=6
echo '{"powmin":3,"powmax":6}' | kubectl exec -i kafka-consumer -- kafka-console-producer --bootstrap-server kafka:9092 --topic jogo-da-vida
```

### Monitor Processing

```bash
# Watch the application logs in real-time
kubectl logs -f openmp-kafka-app-66d9f5487-9q4fh

# You should see:
# [*] Mensagem recebida: {'powmin': 3, 'powmax': 6}
# [*] Resultado da execução:
# tam=8, tempos: init=0.0000029, comp=0.1483381, fim=0.0000060, tot=0.1483469
# [*] Telemetria enviada: {'tam': 8, 'init': 2.9e-06, 'comp': 0.1483381, 'fim': 6e-06, 'tot': 0.1483469}
```

### Check Output Topic

```bash
# Check the telemetry output in the output topic
kubectl exec -it kafka-consumer -- kafka-console-consumer --bootstrap-server kafka:9092 --topic jogo-da-vida-output --from-beginning

# You should see JSON telemetry like:
# {"tam": 8, "init": 2.9e-06, "comp": 0.1483381, "fim": 6e-06, "tot": 0.1483469}
# {"tam": 16, "init": 0.0, "comp": 0.001797, "fim": 1e-06, "tot": 0.0017979}
# {"tam": 32, "init": 9.1e-06, "comp": 0.0002041, "fim": 0.0, "tot": 0.0002131}
# {"tam": 64, "init": 8.1e-06, "comp": 0.0009079, "fim": 0.0, "tot": 0.000916}
```

## 🔍 Understanding the Results

### Input Message Format

```json
{ "powmin": 3, "powmax": 6 }
```

- `powmin=3`: Start with 2³ = 8 grid size
- `powmax=6`: End with 2⁶ = 64 grid size

### Output Telemetry Format

```json
{
  "tam": 8, // Grid size (2^power)
  "init": 2.9e-6, // Initialization time (seconds)
  "comp": 0.1483381, // Computation time (seconds)
  "fim": 6e-6, // Finalization time (seconds)
  "tot": 0.1483469 // Total time (seconds)
}
```

## 🔧 Quick Troubleshooting

### If Pods Don't Start

```bash
kubectl describe pod <pod-name>
# Check for resource constraints or image pull issues
```

### If No Messages Are Processed

```bash
# Check if topics exist
kubectl exec -it kafka-consumer -- kafka-topics --bootstrap-server kafka:9092 --list

# Verify Kafka connectivity
kubectl logs <pod-name> | grep "conectado ao broker"
```

### Clean Kafka Topics (if needed)

```bash
# Delete topics to start fresh
kubectl exec -it kafka-consumer -- kafka-topics --bootstrap-server kafka:9092 --delete --topic jogo-da-vida
kubectl exec -it kafka-consumer -- kafka-topics --bootstrap-server kafka:9092 --delete --topic jogo-da-vida-output
```

## 🎉 Success Indicators

✅ **Deployment**: 2 pods running  
✅ **Kafka Connection**: "Consumidor conectado" message in logs  
✅ **Message Processing**: "[*] Mensagem recebida" in logs  
✅ **OpenMP Execution**: Multiple "tam=" entries showing different grid sizes  
✅ **Telemetry Output**: JSON messages in `jogo-da-vida-output` topic

Your OpenMP Kafka application is now successfully deployed and processing messages! 🚀
