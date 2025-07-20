# Use the official Apache Spark Python image
FROM apache/spark-py:v3.3.0

# Switch to root user to install additional packages
USER root

# Install additional Python packages
RUN pip install --no-cache-dir \
    kafka-python==2.0.2 \
    numpy==1.24.3

# Copy the application
COPY main.py /opt/spark/work-dir/

# Switch back to spark user
USER 185

# Set working directory
WORKDIR /opt/spark/work-dir

# Use a simpler approach - run Python directly
CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[*]", \
     "--conf", "spark.sql.adaptive.enabled=false", \
     "--conf", "spark.serializer=org.apache.spark.serializer.KryoSerializer", \
     "/opt/spark/work-dir/main.py"] 