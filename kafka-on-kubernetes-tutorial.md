# Running Kafka on Kubernetes: Simple Deployment Tutorial

This tutorial guides you through deploying a simple Kafka instance on Kubernetes for development and testing purposes.

## Prerequisites

- A running Kubernetes cluster (like Minikube or Docker Desktop's Kubernetes)
- `kubectl` command-line tool configured to communicate with your cluster

## 🚀 Quick Deployment

The YAML files are already configured in the `/kafka` directory. Simply deploy them:

```bash
# Deploy all Kafka components
kubectl apply -f kafka/

# Check deployment status
kubectl get pods

# Wait for both pods to be running:
# zookeeper-0   1/1     Running
# kafka-0       1/1     Running
```

## 🔍 What Gets Deployed

### ZooKeeper Components

- **Service**: `zookeeper` (ClusterIP) - Provides stable DNS endpoint
- **StatefulSet**: Single ZooKeeper instance with persistent storage

### Kafka Components

- **Service**: `kafka` (Headless) - Enables direct broker connections
- **StatefulSet**: Single Kafka broker with persistent storage

## 🧪 Testing the Deployment

### Create a Test Consumer Pod

```bash
# Create a temporary pod with Kafka tools
kubectl run kafka-consumer --image=confluentinc/cp-kafka:7.5.0 --rm -it --restart=Never -- /bin/sh

# Inside the pod, create a test topic
kafka-topics --bootstrap-server kafka:9092 --create --topic my-test-topic --partitions 1 --replication-factor 1

# Start a consumer
kafka-console-consumer --bootstrap-server kafka:9092 --topic my-test-topic
```

### Send Test Messages

In another terminal:

```bash
# Create a producer pod
kubectl run kafka-producer --image=confluentinc/cp-kafka:7.5.0 --rm -it --restart=Never -- /bin/sh

# Inside the pod, send messages
kafka-console-producer --bootstrap-server kafka:9092 --topic my-test-topic
# Type some messages and press Enter
```

## 🔧 Key Configuration

- **Kafka Address**: `kafka:9092` (for other pods in the cluster)
- **ZooKeeper Address**: `zookeeper:2181`
- **Auto Topic Creation**: Enabled for easy testing
- **Persistent Storage**: 5Gi for Kafka, 2Gi each for ZooKeeper data/logs

## 🎯 Success Indicators

✅ **Pods Running**: Both `zookeeper-0` and `kafka-0` show `Running` status  
✅ **Topics Created**: Can create topics without errors  
✅ **Message Flow**: Producer can send, consumer can receive messages

Your Kafka cluster is now ready for other applications to connect using `kafka:9092`! 🚀
