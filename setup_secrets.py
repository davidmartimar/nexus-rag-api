
import os

def setup_secrets():
    # 1. Create .streamlit directory
    secrets_dir = os.path.join("frontend", ".streamlit")
    os.makedirs(secrets_dir, exist_ok=True)
    
    # 2. Create secrets.toml
    secrets_file = os.path.join(secrets_dir, "secrets.toml")
    secrets_content = '[general]\npassword = "Ne1Da2"'
    
    with open(secrets_file, "w") as f:
        f.write(secrets_content)
    print(f"Created {secrets_file}")
    
    # 3. Update .gitignore
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
            
        if "secrets.toml" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# --- Secrets ---\nfrontend/.streamlit/secrets.toml\n")
            print("Updated .gitignore")
        else:
            print(".gitignore already contains secrets.toml")

if __name__ == "__main__":
    setup_secrets()
