
import os
import uuid

def update_env():
    env_path = ".env"
    key_name = "NEXUS_API_KEY"
    
    # Generate a strong key
    new_key = f"sk-{uuid.uuid4()}"
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
            
        if key_name in content:
            print(f"{key_name} already exists in .env")
        else:
            with open(env_path, "a") as f:
                # Ensure newline
                if not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{key_name}={new_key}\n")
            print(f"Added {key_name} to .env: {new_key}")
    else:
        with open(env_path, "w") as f:
            f.write(f"{key_name}={new_key}\n")
        print(f"Created .env with {key_name}: {new_key}")

if __name__ == "__main__":
    update_env()
