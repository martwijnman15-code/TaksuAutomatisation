from .runtime import mydb, os, subprocess


# laravel operations

def insert_laravel_database():
    mycursor = mydb.cursor()

    mycursor.execute(f"CREATE DATABASE IF NOT EXISTS `laravel_projects`")
    mycursor.execute(f"USE `laravel_projects`")

    query = """
        CREATE TABLE IF NOT EXISTS frontend_projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            backend_project_id INT NOT NULL,
            project_name VARCHAR(255) NOT NULL,
            path VARCHAR(255) NOT NULL
        )
    """

    query2 = """
        CREATE TABLE IF NOT EXISTS backend_projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(255) NOT NULL,
            path VARCHAR(255) NOT NULL
        )
    """

    query3 = """
        CREATE TABLE IF NOT EXISTS model_projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            model_name VARCHAR(255) NOT NULL,
            backend_project_id INT NOT NULL
        )
    """

    mycursor.execute(query)
    mycursor.execute(query2)
    mycursor.execute(query3)
    mydb.commit()

    os.makedirs("projects/backend_projects", exist_ok=True)
    os.makedirs("projects/frontend_projects", exist_ok=True)

def index_laravel():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute(f"USE `laravel_projects`")
    mycursor.execute("SELECT * FROM `backend_projects`")
    projects = mycursor.fetchall()

    mycursor.close()
    return projects

def select_laravel(id):
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("USE `laravel_projects`")

    mycursor.execute(
        "SELECT * FROM `backend_projects` WHERE id = %s",
        (id,)
    )
    backend_project = mycursor.fetchone()

    mycursor.execute(
        "SELECT * FROM `frontend_projects` WHERE backend_project_id = %s",
        (id,)
    )
    frontend_projects = mycursor.fetchall()

    mycursor.close()

    return frontend_projects, backend_project

def create_laravel(project_name, database, php_type, path):
    command = [
        "laravel",
        "new",
        project_name,
        f"--database={database}",
        f"--{php_type}"
    ]

    subprocess.run(command, check=True)

    subprocess.run(
    ["php", "artisan", "install:api", "--no-interaction"],
    cwd=project_name,
    check=True,)

    mycursor = mydb.cursor()
    mycursor.execute(f"USE `laravel_projects`")
    mycursor.execute(f"INSERT INTO backend_projects VALUES (" + project_name + ", " + path + ");")

    mydb.commit()
    mycursor.close()

def laravel_create_crud(project_id, project_name, model_name):
    subprocess.run(
        ["php", "artisan", "make:model", model_name, "-s"],
        cwd=project_name,
        check=True,)

    migration = "create_" + model_name + "s_table"

    subprocess.run(
        ["php", "artisan", "make:migration", migration],
        cwd=project_name,
        check=True)

    subprocess.run(
        [
            "php", "artisan", "make:controller",
            f"Api/{model_name}Controller",
            "--api",
            f"--model={model_name}",
        ],
        cwd=project_name,
        check=True,
    )
    mycursor = mydb.cursor()
    mycursor.execute(f"USE `model_projects`")
    mycursor.execute(f"INSERT INTO model_projects VALUES (" + model_name + ", " + project_id + ");")

    mydb.commit()
    mycursor.close()

def download_package_laravel(project_name, package, dev=False):
    command = ["composer", "require"]

    if dev:
        command.append("--dev")

    command.append(package)

    subprocess.run(
        command,
        cwd=project_name,
        check=True,
    )

def index_frontend():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("SELECT * FROM `frontend_projects`")
    projects = mycursor.fetchall()

def laravel_create_crud(project_name, model_name):
    subprocess.run(
        ["php", "artisan", "make:model", model_name, "-m -s"],
        cwd=project_name,
        check=True,)

    subprocess.run(
        [
            "php", "artisan", "make:controller",
            f"Api/{model_name}Controller",
            "--api",
            f"--model={model_name}",
        ],
        cwd=project_name,
        check=True,
    )

def download_package_laravel(project_name, package, dev=False):
    command = ["composer", "require"]

    if dev:
        command.append("--dev")

    command.append(package)

    subprocess.run(
        command,
        cwd=project_name,
        check=True,
    )

    mycursor.close()

    return projects
