# Deploying ELK Stack (Elasticsearch + Kibana) on Kubernetes

This tutorial shows how to deploy Elasticsearch and Kibana to complete your data pipeline and create dashboards for telemetry visualization.

## 🎯 What We're Deploying

- **Elasticsearch** for storing and indexing telemetry data
- **Kibana** for creating dashboards and data visualization
- **Complete data pipeline**: OpenMP App → Kafka → Output Consumer → Elasticsearch → Kibana
- **New JSON schema** following the structure defined in `log.jsonc`

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

# (Optional) Deploy enhanced index mapping for better performance
kubectl apply -f elasticsearch/index-mapping.yaml
kubectl apply -f elasticsearch/elasticsearch-init-job.yaml

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

### Step 5: (Optional) Deploy Kibana Index Pattern

If you deployed the enhanced configuration:

```bash
# Deploy Kibana index pattern configuration
kubectl apply -f kibana/kibana-index-pattern.yaml

# Check if the init job completed successfully
kubectl get jobs
kubectl logs job/elasticsearch-init
```

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
# [*] Mensagem recebida: {'game_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'step': 1, 'total_steps': 3, 'board_size': 8, 'start_time': 1700000000, 'end_time': 1700000002, 'impl': 'openmp'}
# [*] Enviado para Elasticsearch: {'game_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'step': 1, 'total_steps': 3, 'board_size': 8, 'start_time': 1700000000, 'end_time': 1700000002, 'impl': 'openmp', 'timestamp': '2024-01-15T10:30:45.123456'}
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
   - `game_id` (unique session identifier)
   - `step` (current step number)
   - `total_steps` (total steps in session)
   - `board_size` (matrix size)
   - `start_time` (step start time)
   - `end_time` (step end time)
   - `impl` (implementation type: openmp/spark)
   - `timestamp` (processing timestamp)

### Step 3: Create Visualizations

1. Go to **Analytics > Visualize Library**
2. Click **Create visualization**
3. Example visualizations:
   - **Line chart**: Step duration (`end_time - start_time`) over time
   - **Bar chart**: Average step duration by `board_size` (matrix size)
   - **Pie chart**: Distribution of steps by `impl` (implementation type)
   - **Data table**: Game sessions with `game_id`, `step`, and `board_size`
   - **Metric**: Total number of completed steps
   - **Histogram**: Distribution of `board_size` values

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

## ⚡ Enhanced Features (Optional Configuration)

If you deployed the enhanced configuration files, you get:

### **Better Data Types**

- `start_time`/`end_time` → Proper date fields for time-based analysis
- `game_id`/`impl` → Keyword fields for efficient filtering and grouping
- Automatic `duration` calculation from start/end times

### **Performance Optimizations**

- Optimized index mapping for faster queries
- Reduced storage overhead with proper field types
- Better aggregation performance

### **Rich Analytics**

- Group steps by game session using `game_id`
- Compare performance between `impl` types (openmp vs spark)
- Track step progression within game sessions
- Time-series analysis of step durations
- Performance correlation with `board_size`

### **Example Advanced Queries**

```json
// Average step duration by board size
GET /jogo-da-vida-telemetry/_search
{
  "aggs": {
    "by_board_size": {
      "terms": { "field": "board_size" },
      "aggs": {
        "avg_duration": {
          "avg": {
            "script": "doc['end_time'].value.toInstant().toEpochMilli() - doc['start_time'].value.toInstant().toEpochMilli()"
          }
        }
      }
    }
  }
}
```

## 📈 Next Steps

- Create more complex visualizations using the new field structure
- Set up alerts for performance thresholds using step duration
- Explore Kibana's machine learning features for anomaly detection
- Compare performance between OpenMP and Spark implementations
- Scale Elasticsearch horizontally if needed
