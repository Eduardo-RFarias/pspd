# Running Kafka on Kubernetes: A Simple Tutorial

This tutorial guides you through deploying a simple, single-broker Kafka instance on Kubernetes. This setup is intended for development and learning purposes, demonstrating how to make Kafka accessible to other applications within the same cluster.

We will use `StatefulSet` resources for both ZooKeeper and Kafka to provide stable network identifiers and storage, which is crucial for stateful applications.

---

### Prerequisites

- A running Kubernetes cluster (like Minikube or Docker Desktop's Kubernetes).
- `kubectl` command-line tool configured to communicate with your cluster.

---

### Step 1: Create ZooKeeper Resources

Kafka relies on ZooKeeper for cluster management. First, we need to deploy a single-node ZooKeeper instance.

Create the following two files in a directory named `kafka`.

#### `kafka/zookeeper-service.yaml`

This file defines a `ClusterIP` service that provides a stable DNS endpoint (`zookeeper`) for other pods to reach the ZooKeeper instance.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: zookeeper
spec:
  ports:
    - port: 2181
      name: client
  selector:
    app: zookeeper
```

#### `kafka/zookeeper-statefulset.yaml`

This `StatefulSet` manages the ZooKeeper pod. It uses a `PersistentVolumeClaim` to ensure that ZooKeeper's data persists across restarts.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: zookeeper
spec:
  serviceName: zookeeper
  replicas: 1
  selector:
    matchLabels:
      app: zookeeper
  template:
    metadata:
      labels:
        app: zookeeper
    spec:
      containers:
        - name: zookeeper
          image: confluentinc/cp-zookeeper:7.5.0
          ports:
            - containerPort: 2181
          env:
            - name: ZOOKEEPER_CLIENT_PORT
              value: "2181"
            - name: ZOOKEEPER_TICK_TIME
              value: "2000"
      volumeMounts:
        - name: zookeeper-data
          mountPath: /var/lib/zookeeper/data
        - name: zookeeper-log
          mountPath: /var/lib/zookeeper/log
  volumeClaimTemplates:
    - metadata:
        name: zookeeper-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 2Gi
    - metadata:
        name: zookeeper-log
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 2Gi
```

---

### Step 2: Create Kafka Resources

Now, let's deploy Kafka itself. This also consists of a service and a stateful set.

#### `kafka/kafka-headless-service.yaml`

We create a headless service for Kafka. This is important because it provides a unique DNS entry for each Kafka broker pod, allowing clients to connect to a specific broker directly. This is different from a regular service that load-balances requests.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka
spec:
  clusterIP: None
  ports:
    - name: kafka
      port: 9092
  selector:
    app: kafka
```

#### `kafka/kafka-statefulset.yaml`

This `StatefulSet` deploys a single Kafka broker. Key configurations include:

- Connecting to ZooKeeper using the service name `zookeeper`.
- Advertising its address within the cluster as `kafka-0.kafka:9092` so other pods can find it.
- Enabling auto-creation of topics for easy testing (not recommended for production).

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
        - name: kafka
          image: confluentinc/cp-kafka:7.5.0
          ports:
            - containerPort: 9092
          env:
            - name: KAFKA_BROKER_ID
              value: "1"
            - name: KAFKA_ZOOKEEPER_CONNECT
              value: "zookeeper:2181"
            - name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP
              value: "PLAINTEXT:PLAINTEXT"
            - name: KAFKA_ADVERTISED_LISTENERS
              value: "PLAINTEXT://kafka-0.kafka:9092"
            - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
              value: "1"
            - name: KAFKA_AUTO_CREATE_TOPICS_ENABLE
              value: "true"
      volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
  volumeClaimTemplates:
    - metadata:
        name: kafka-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
```

---

### Step 3: Apply the YAML files

With all the files created in the `kafka/` directory, apply them to your Kubernetes cluster:

```sh
kubectl apply -f kafka/
```

This command will create all the services, statefulsets, and persistent volume claims.

You can check the status of the pods:

```sh
kubectl get pods
```

Wait until both `zookeeper-0` and `kafka-0` pods are in the `Running` state.
This completes the Kafka deployment. Other pods in the cluster can now connect to Kafka using the address `kafka:9092`.
