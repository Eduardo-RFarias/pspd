# Deploying ELK Stack (Elasticsearch + Kibana) on Kubernetes

This tutorial shows how to deploy Elasticsearch and Kibana to complete your data pipeline and create dashboards for telemetry visualization.

## 🎯 What We're Deploying

- **Elasticsearch** for storing and indexing telemetry data
- **Kibana** for creating dashboards and data visualization
- **Complete data pipeline**: OpenMP App → Kafka → Output Consumer → Elasticsearch → Kibana

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or similar)
- Kafka and OpenMP App already deployed
- Output Consumer already deployed

## 🚀 Deployment Steps

### Step 1: Deploy Elasticsearch

Elasticsearch needs to be deployed first since Kibana depends on it:

```bash
# Deploy Elasticsearch StatefulSet and Service
kubectl apply -f elasticsearch/elasticsearch-statefulset.yaml
kubectl apply -f elasticsearch/elasticsearch-service.yaml

# Check Elasticsearch status
kubectl get statefulset elasticsearch
kubectl get pods -l app=elasticsearch
```

You should see something like:

```
NAME            READY   AGE
elasticsearch   1/1     30s

NAME                READY   STATUS    RESTARTS   AGE
elasticsearch-0     1/1     Running   0          30s
```

### Step 2: Wait for Elasticsearch to be Ready

```bash
# Watch Elasticsearch logs
kubectl logs elasticsearch-0 -f

# Look for this success message:
# "started [Cluster health status changed from [RED] to [YELLOW]]"
```

### Step 3: Deploy Kibana

Once Elasticsearch is running, deploy Kibana:

```bash
# Deploy Kibana Deployment and Service (NodePort)
kubectl apply -f kibana/kibana-deployment.yaml
kubectl apply -f kibana/kibana-service.yaml

# Check Kibana status
kubectl get deployment kibana
kubectl get pods -l app=kibana
kubectl get svc kibana
```

You should see the service configured as ClusterIP:

```
NAME     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
kibana   ClusterIP   10.111.102.67   <none>        5601/TCP   2m
```

### Step 4: Access Kibana

```bash
# Forward Kibana port to localhost (run in background)
kubectl port-forward svc/kibana 5601:5601
```

Then open your browser and go to: **http://localhost:5601**

## 🧪 Testing the Complete Pipeline

### Test Step 1: Send Test Message to OpenMP App

```bash
# Send test message to trigger the entire pipeline
echo '{"powmin":3,"powmax":5}' | kubectl exec -i kafka-consumer -- kafka-console-producer --bootstrap-server kafka:9092 --topic jogo-da-vida
```

### Test Step 2: Verify Data Flow

```bash
# Check output-consumer logs (should show successful Elasticsearch sends)
kubectl logs -l app=output-consumer-app -f

# You should see:
# [*] Mensagem recebida: {'tam': 8, 'init': 2.9e-06, 'comp': 0.1483381, 'fim': 6e-06, 'tot': 0.1483469}
# [*] Enviado para Elasticsearch: {'tam': 8, 'init': 2.9e-06, 'comp': 0.1483381, 'fim': 6e-06, 'tot': 0.1483469, 'timestamp': '2024-01-15T10:30:45.123456'}
```

### Test Step 3: Access Kibana Dashboard

```bash
# Universal method: Port forwarding (run in background)
kubectl port-forward svc/kibana 5601:5601
```

Then open your browser and go to: **http://localhost:5601**

You should see the Kibana welcome screen!

## 📊 Creating Your First Dashboard

### Step 1: Create Index Pattern

1. In Kibana, go to **Management > Stack Management > Index Patterns**
2. Click **Create index pattern**
3. Enter pattern: `jogo-da-vida-telemetry*`
4. Click **Next step**
5. Select **timestamp** as the time field
6. Click **Create index pattern**

### Step 2: Explore Your Data

1. Go to **Analytics > Discover**
2. Select your `jogo-da-vida-telemetry*` index pattern
3. You should see your telemetry data with fields:
   - `tam` (matrix size)
   - `init` (initialization time)
   - `comp` (computation time)
   - `fim` (finalization time)
   - `tot` (total time)
   - `timestamp`

### Step 3: Create Visualizations

1. Go to **Analytics > Visualize Library**
2. Click **Create visualization**
3. Example visualizations:
   - **Line chart**: `tot` (total time) over time
   - **Bar chart**: Average `comp` time by `tam` (matrix size)
   - **Metric**: Latest values of execution times

### Step 4: Build Dashboard

1. Go to **Analytics > Dashboard**
2. Click **Create dashboard**
3. Add your visualizations
4. Save your dashboard

## 🔍 Understanding the Complete Data Flow

```
Input → [OpenMP App] → Kafka → [Output Consumer] → Elasticsearch → Kibana → Browser
  ↑           ↑          ↑            ↑               ↑           ↑         ↑
JSON      Processes   Topics     Enriches        Indexes    Visualizes  You!
```

## 🔧 Troubleshooting

### Check Component Status

```bash
# Check all pods are running
kubectl get pods

# Check Elasticsearch health
kubectl exec elasticsearch-0 -- curl -X GET "localhost:9200/_cluster/health?pretty"

# Check if data is indexed
kubectl exec elasticsearch-0 -- curl -X GET "localhost:9200/jogo-da-vida-telemetry/_search?size=3&pretty"
```

### Troubleshoot Port Forwarding

```bash
# If localhost:5601 doesn't work, restart port forwarding:
# Stop: Ctrl+C in the port-forward terminal
# Start: kubectl port-forward svc/kibana 5601:5601
```

## 🎉 Success Indicators

✅ **All pods running**: `kubectl get pods`  
✅ **Data pipeline working**: OpenMP → Kafka → Consumer → Elasticsearch  
✅ **Kibana accessible**: http://localhost:5601  
✅ **Data indexed**: Telemetry visible in Elasticsearch  
✅ **Dashboard ready**: Create index patterns and visualizations

Your complete ELK stack is now running! 🚀

## 📈 Next Steps

- Create more complex visualizations
- Set up alerts for performance thresholds
- Explore Kibana's machine learning features
- Scale Elasticsearch horizontally if needed
