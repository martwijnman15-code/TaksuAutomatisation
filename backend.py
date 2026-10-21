import subprocess


#laravel operations
def create_laravel(project_name, database, frontend, theme):
    subprocess.run(["composer",
    "create-project",
    "laravel/laravel",
     project_name,
     database,
     frfrontendontend,
     theme
     ], check=True)

def laravel_create_crud(project_name, model_name):
    subprocess.run(
        ["bash", "laravel_create_crud.sh", project_name, model_name],
        check=True
    )

#gitea operations
