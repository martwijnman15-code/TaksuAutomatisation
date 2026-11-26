from .runtime import mydb, os, subprocess


def create_frontend(framework, backend_project_id, project_name, path="projects/frontend_projects"):
    framework = framework.lower() # put everything in lowercase
    path = os.path.abspath(path) # puth the path for the terminal

    os.makedirs(path, exist_ok=True)

    # React
    if framework == "react":
        command = [
            "npx", "--yes", "create-vite@latest",
            project_name, "--template", "react"
        ]

    # React Admin
    elif framework == "react-admin":
        command = [
            "npx", "--yes", "create-react-admin@latest",
            project_name
        ]

    # Expo
    elif framework == "expo":
        command = [
            "npx", "--yes", "create-expo-app@latest",
            project_name, "--yes"
        ]

    # Next.js
    elif framework == "nextjs":
        command = [
            "npx", "--yes", "create-next-app@latest",
            project_name, "--yes"
        ]

    else:
        raise ValueError(f"Unsupported framework: {framework}")

    subprocess.run(command, cwd=path, check=True)

    # Full project path
    project_path = os.path.join(path, project_name)

    # Save project in MySQL
    mycursor = mydb.cursor()
    mycursor.execute("USE `laravel_projects`")

    query = """
        INSERT INTO frontend_projects
        (backend_project_id, project_name)
        VALUES (%s, %s)
    """

    mycursor.execute(query, (
        backend_project_id,
        project_name
    ))

    mydb.commit()

    mycursor.close()

    return project_path

def download_package_frontend(name):
    subprocess.run(["npm", "install", name], check=True)

def run_frontend():
    subprocess.run(["npm", "run", "dev"], check=True)

def run_backend():
    subprocess.run(["php", "artisan", "serve"], check=True)
