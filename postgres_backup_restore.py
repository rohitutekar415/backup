import os
import subprocess
import time

# Database credentials
PG_USER = "postgres"
PG_PASSWORD = "mysecretpassword"
DB_NAME = "mydb"
BACKUP_DIR = "/backup"
SCHEMA_FILE = f"{BACKUP_DIR}/schema.sql"

# Function to check if PostgreSQL is ready
def wait_for_postgres():
    while True:
        try:
            subprocess.run(
                f"PGPASSWORD={PG_PASSWORD} psql -h localhost -U {PG_USER} -d {DB_NAME} -c 'SELECT 1;'",
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ PostgreSQL is ready!")
            return
        except subprocess.CalledProcessError:
            print("⏳ Waiting for PostgreSQL to be ready...")
            time.sleep(2)

# Function to backup database tables and schema
def backup_database():
    print("📦 Taking backup of database in CSV format...")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Backup schema
    try:
        subprocess.run(
            f"PGPASSWORD={PG_PASSWORD} pg_dump -h localhost -U {PG_USER} -d {DB_NAME} --schema-only > {SCHEMA_FILE}",
            shell=True,
            check=True
        )
        print("✅ Database schema backed up successfully!")
    except subprocess.CalledProcessError as e:
        print("❌ Error backing up schema!", e)
        return

    # Get list of tables
    try:
        result = subprocess.run(
            f"PGPASSWORD={PG_PASSWORD} psql -h localhost -U {PG_USER} -d {DB_NAME} -t -c \"SELECT tablename FROM pg_tables WHERE schemaname='public';\"",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        tables = [table.strip() for table in result.stdout.split("\n") if table.strip()]
        
        if not tables:
            print("❌ No tables found in the database.")
            return
        
        for table in tables:
            print(f"🔄 Backing up table: {table}")
            backup_file = f"{BACKUP_DIR}/{table}.csv"
            
            try:
                subprocess.run(
                    f"PGPASSWORD={PG_PASSWORD} psql -h localhost -U {PG_USER} -d {DB_NAME} -c \"\\copy {table} TO '{backup_file}' WITH CSV HEADER;\"",
                    shell=True,
                    check=True
                )
                print(f"✅ Table {table} backed up successfully!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error backing up table {table}: {e}")
    except subprocess.CalledProcessError:
        print("❌ Failed to retrieve table names!")

# Function to restore database tables and schema
def restore_database():
    print("♻️ Restoring database from backup files...")
    if not os.path.exists(BACKUP_DIR):
        print(f"❌ Backup directory {BACKUP_DIR} not found!")
        return
    
    if not os.path.exists(SCHEMA_FILE):
        print("❌ Schema backup file not found!")
        return
    
    # Restore schema
    try:
        subprocess.run(
            f"PGPASSWORD={PG_PASSWORD} psql -h localhost -U {PG_USER} -d {DB_NAME} -f {SCHEMA_FILE}",
            shell=True,
            check=True
        )
        print("✅ Database schema restored successfully!")
    except subprocess.CalledProcessError as e:
        print("❌ Error restoring schema!", e)
        return
    
    csv_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".csv")]
    if not csv_files:
        print("❌ No backup files found!")
        return
    
    for csv_file in csv_files:
        table_name = os.path.splitext(csv_file)[0]
        backup_file = os.path.join(BACKUP_DIR, csv_file)
        print(f"🔄 Restoring table: {table_name}")
        
        restore_cmd = f"""
        PGPASSWORD={PG_PASSWORD} psql -h localhost -U {PG_USER} -d {DB_NAME} -c "\\copy {table_name} FROM '{backup_file}' WITH CSV HEADER;"
        """
        try:
            subprocess.run(restore_cmd, shell=True, check=True)
            print(f"✅ Table {table_name} restored successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error restoring table {table_name}: {e}")

if __name__ == "__main__":
    wait_for_postgres()
    mode = os.getenv("MODE", "backup").strip().lower()
    
    if mode == "backup":
        backup_database()
    elif mode == "restore":
        restore_database()
    else:
        print("❌ Invalid MODE. Use 'backup' or 'restore'.")
