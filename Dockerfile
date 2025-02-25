# Use official PostgreSQL image
FROM postgres:15

# Install Python inside the container
RUN apt-get update && apt-get install -y python3 python3-pip

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=mysecretpassword
ENV POSTGRES_DB=mydb
ENV BACKUP_DIR=/backup
ENV MODE=restore

# Set working directory
WORKDIR /app

# Copy restore script
COPY postgres_backup_restore.py /app/postgres_backup_restore.py

# Ensure backup directory exists and set correct permissions
RUN mkdir -p ${BACKUP_DIR} && chmod 777 ${BACKUP_DIR}

# Set execution permission for restore script
RUN chmod +x /app/postgres_backup_restore.py

# Expose PostgreSQL port
EXPOSE 5432

# Start PostgreSQL, wait for it to be ready, then run the restore script
CMD ["sh", "-c", "docker-entrypoint.sh postgres & sleep 5; \
    until pg_isready -h localhost -p 5432 -U $POSTGRES_USER; do sleep 2; done; \
    python3 /app/postgres_backup_restore.py && tail -f /dev/null"]
