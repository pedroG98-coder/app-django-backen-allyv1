from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
)
from land import serializers, models, helpers
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from land.serializers import MyTokenObtainPairSerializer
from django.http import JsonResponse
import re


def index(request):
    return render(request, "land/index.html")


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# ==========================================================================================================================
# Vista Lista Para Modelo Usuario
# ==========================================================================================================================


class UsuarioLista(APIView, LimitOffsetPagination):
    permission_classes = [AllowAny]

    def get(self, request):
        objects = models.User.objects.filter(estatus_sistema=True)
        results = self.paginate_queryset(objects, request, view=self)
        serializer = serializers.UserDepthSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):

        # Validamos el formato del correo electrónico
        email = request.data.get("email").lower()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response(
                {"error": ["Ingrese un correo válido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos el correo electrónico
        email = request.data.get("email").lower()
        if models.User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "El correo electrónico ya está en uso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos el nombre de usuario
        username = request.data.get("username").lower()
        if models.User.objects.filter(username__iexact=username).exists():
            return Response(
                {"error": ["El username ya está en uso"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos la longitud username
        if len(username) < 8:
            return Response(
                {"error": "El username debe tener al menos 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos el nombre completo
        nombre_completo = request.data.get("nombre_completo")
        if not nombre_completo or len(nombre_completo) < 5:
            return Response(
                {"error": "El nombre completo debe tener al menos 5 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos que el nombre completo contenga letras
        if not re.search(r"[a-zA-Z]", nombre_completo):
            return Response(
                {"error": "El nombre completo debe contener al menos una letra."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos que el nombre completo no contenga caracteres no permitidos
        if re.match(r"^[\sA-Za-záéíóúÁÉÍÓÚñÑ]+$", nombre_completo) is None:
            return Response(
                {"error": "El nombre completo contiene caracteres no válidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # *****************************************""

        # Validación de las contraseñas
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        if password != confirm_password:
            return Response(
                {"error": "Las contraseñas no coinciden"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verifica que la contraseña no sea vacía
        if not password:
            return Response(
                {"error": "La contraseña no puede estar vacía."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verifica el mínimo de caracteres
        if len(password) < 8:
            return Response(
                {"error": "La contraseña debe tener al menos 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validación del formato de la contraseña
        if password.isdigit():
            return Response(
                {"error": "La contraseña no debe ser numéricamente solamente"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validamos si la contraseña es solo numérica usando una expresión regular
        if re.match(r"^\d+$", password):
            return Response(
                {
                    "error": "La contraseña debe contener al menos un carácter alfabético. No puede ser solo numérica."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializers.UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data["password"] = make_password(password)
            user = serializer.save(is_active=True)
            return Response(
                serializers.UserDepthSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================================================================================================
# Vista Detalle Para Modelo Usuario
# ==========================================================================================================================


class UsuarioDetalle(APIView):

    permission_classes = [AllowAny]

    def get_object(self, pk):
        model_object = get_object_or_404(models.User, pk=pk)
        return model_object

    def get(self, request, pk):
        model_object = self.get_object(pk)
        serializer = serializers.UserDepthSerializer(model_object)
        return Response(serializer.data)

    def put(self, request, pk):
        model_object = self.get_object(pk)
        serializer = serializers.UserSerializer(model_object, data=request.data)
        password = request.data.get("password")
        if serializer.is_valid():
            if password is not None:
                pwrd = make_password(password)
                serializer.password = pwrd
                serializer.save()
                id_user = serializer.data.get("id")
                user = models.User.objects.get(id=id_user)
                user.password = pwrd
                user.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        model_object = self.get_object(pk)
        model_object.estatus_sistema = False
        model_object.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================================================================================
# Vista Lista Para Modelo Tarea
# ==========================================================================================================================


class TareaLista(APIView, LimitOffsetPagination):
    """
    -Get retorna todos los registros en la bd con estatus en sistema = True
    -Post permite crear un nuevo registro en la base de datos
    """

    permission_classes = [AllowAny]

    def get(self, request):
        objects = models.Tarea.objects.filter(estatus_sistema=True)
        results = self.paginate_queryset(objects, request, view=self)
        serializer = serializers.TareaDepthSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = serializers.TareaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================================================================================================
# Vista Detalle Para Modelo Usuario
# ==========================================================================================================================


class TareaDetalle(APIView):

    permission_classes = [AllowAny]

    def get_object(self, pk):
        objeto = get_object_or_404(models.Tarea, pk=pk)
        return objeto

    def get(self, request, pk):
        objeto = self.get_object(pk)
        serializer = serializers.TareaDepthSerializer(objeto)
        return Response(serializer.data)

    def put(self, request, pk):
        model_object = self.get_object(pk)
        serializer = serializers.TareaSerializer(model_object, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        objeto = self.get_object(pk)
        objeto.estatus_sistema = False
        objeto.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================================================================================
# Vista Metodo Tiempo Restante Tarea
# ==========================================================================================================================


class GETTiempoRestante(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tarea_id):
        try:
            tarea = models.Tarea.objects.get(id=tarea_id)
            tiempo_restante = helpers.get_tiempo_restante(tarea)
            return JsonResponse({"tiempo_restante": tiempo_restante})
        except models.Tarea.DoesNotExist:
            return JsonResponse({"error": "Tarea no encontrada"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
