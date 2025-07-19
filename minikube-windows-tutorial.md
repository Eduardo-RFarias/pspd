# Minikube Installation & Cluster Initialization on Windows (with Docker Desktop)

This guide walks you through installing Minikube and initializing a Kubernetes cluster on Windows, using Docker Desktop as the container driver. Based on the [official Minikube documentation](https://minikube.sigs.k8s.io/docs/start/?arch=%2Fwindows%2Fx86-64%2Fstable%2F.exe+download).

---

## 1. Prerequisites

- **Windows 10/11 (x86-64)**
- **Docker Desktop** (already installed and running)
- **2 CPUs or more**
- **2GB+ RAM**
- **20GB+ free disk space**
- **Internet connection**

---

## 2. Download and Install Minikube

### a. Download the Minikube executable

- Go to the [Minikube releases page](https://github.com/kubernetes/minikube/releases/latest) and download `minikube-windows-amd64.exe`.
- Rename the downloaded file to `minikube.exe`.

### b. Move the executable

- Create a directory for Minikube (e.g., `C:\minikube`).
- Move `minikube.exe` into `C:\minikube`.

### c. Add Minikube to your PATH

Open **PowerShell as Administrator** and run:

```powershell
$oldPath = [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine)
if ($oldPath.Split(';') -inotcontains 'C:\minikube') {
  [Environment]::SetEnvironmentVariable('Path', $('{0};C:\minikube' -f $oldPath), [EnvironmentVariableTarget]::Machine)
}
```

> **Note:** Close and reopen your terminal after this step.

---

## 3. Start Minikube Cluster

Open a new **PowerShell** window (not as Administrator) and run:

```powershell
minikube start --driver=docker
```

- This will start a local Kubernetes cluster using Docker as the container backend.
- The first run may take a few minutes as images are downloaded.

---

## 4. Verify Cluster Status

Check that your cluster is running:

```powershell
minikube status
```

You should see output indicating that the host, kubelet, apiserver, and kubeconfig are all running.

---

## 5. Interact with Your Cluster

### a. Using kubectl

If you have `kubectl` installed, you can use it directly:

```powershell
kubectl get po -A
```

If not, you can use the version bundled with Minikube:

```powershell
minikube kubectl -- get po -A
```

### b. Launch the Kubernetes Dashboard

```powershell
minikube dashboard
```

This will open the Kubernetes dashboard in your browser.

---

## References

- [Minikube Official Start Guide](https://minikube.sigs.k8s.io/docs/start/?arch=%2Fwindows%2Fx86-64%2Fstable%2F.exe+download)
- [Minikube GitHub Releases](https://github.com/kubernetes/minikube/releases/latest)
