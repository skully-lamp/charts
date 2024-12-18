from flask_appbuilder.security.manager import BaseSecurityManager
from airflow.models.serialized_dag import SerializedDagModel
from flask import request
import json


class CustomRBACSecurityManager(BaseSecurityManager):
    """
    Custom Security Manager for Airflow to enforce RBAC-based DAG filtering.
    """

    # Role-to-tag mapping
    ROLE_TAG_MAP = {
        "b2b_viewer": ["b2b"],
        "b2c_viewer": ["b2c"],
        "admin": [],  # Admin can see all DAGs
    }

    def get_user_permissions(self, user):
        """
        Dynamically assign permissions to DAGs based on the user's role.
        """
        # Get the role from the HTTP headers
        role_name = request.headers.get("X-User-Role", "viewer")  # Default to "viewer"
        allowed_tags = self.ROLE_TAG_MAP.get(role_name, [])

        # Fetch all serialized DAGs
        all_dags = SerializedDagModel.read_all_dags()
        user_permissions = {}

        for dag_id, dag_data in all_dags.items():
            dag_tags = set(dag_data.get("tags", []))  # DAG tags

            # Check if the user is allowed to view this DAG
            if not allowed_tags or dag_tags & set(allowed_tags):  # Empty tags mean full access
                user_permissions[dag_id] = {"can_read": True, "can_edit": role_name == "admin"}
            else:
                user_permissions[dag_id] = {"can_read": False, "can_edit": False}

        return user_permissions

    def has_access(self, permission_name, view_name, user):
        """
        Override access checks for filtering DAGs dynamically.
        """
        # Ensure it's a DAG-related view
        if not view_name.startswith("dag"):
            return True  # Allow non-DAG views like Admin or Connections

        # Get user-specific permissions
        user_permissions = self.get_user_permissions(user)
        dag_id = view_name.split(".")[-1]  # Extract the DAG ID

        # Check permissions for the DAG
        if dag_id in user_permissions:
            if permission_name == "can_read" and user_permissions[dag_id]["can_read"]:
                return True
            if permission_name == "can_edit" and user_permissions[dag_id]["can_edit"]:
                return True

        return False  # Default: Deny access



from custom_security_manager import CustomSecurityManager

# Set the custom security manager class
SECURITY_MANAGER_CLASS = CustomSecurityManager
