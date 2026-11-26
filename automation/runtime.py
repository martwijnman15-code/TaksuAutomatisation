import git, os, shutil, subprocess, re
from typing import Annotated
from cryptography.fernet import Fernet
import mysql.connector
import requests

s = requests.Session()
g = git.Git('git-repo')
repo = git.Repo()

mydb = mysql.connector.connect(
    host="localhost",
    user="taksu",
    password="200415",
    database="laravel_projects",
    port=3306
)
