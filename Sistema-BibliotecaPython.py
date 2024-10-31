import os
from collections import deque
import re

class Libro:
    def __init__(self, titulo, autor, año, editorial, isbn, paginas):
        self.titulo = titulo
        self.autor = autor
        self.año = año
        self.editorial = editorial
        self.isbn = isbn
        self.paginas = paginas
        self.siguiente = None

    def validar_isbn(self):
        # Validación básica de ISBN (13 dígitos)
        patron = re.compile(r'^\d{13}$')
        return bool(patron.match(str(self.isbn)))

class PilaAcciones:
    def __init__(self):
        self.acciones = []
        self.estados_previos = []  # Para almacenar estados anteriores

    def apilar(self, accion, estado_anterior=None):
        self.acciones.append(accion)
        self.estados_previos.append(estado_anterior)

    def desapilar(self):
        if self.acciones:
            return self.acciones.pop(), self.estados_previos.pop()
        return "La pila está vacía", None

class ColaSolicitudes:
    def __init__(self):
        self.cola = deque()

    def encolar(self, nombre, dni, titulo_libro):
        self.cola.append((nombre, dni, titulo_libro))

    def desencolar(self):
        return self.cola.popleft() if self.cola else None

    def esta_vacia(self):
        return len(self.cola) == 0

class Biblioteca:
    def __init__(self):
        self.cabeza = None
        self.pila_acciones = PilaAcciones()
        self.solicitudes = {}
        self.cola_espera = ColaSolicitudes()

    def agregar_libro(self, titulo, autor, año, editorial, isbn, paginas):
        nuevo_libro = Libro(titulo, autor, año, editorial, isbn, paginas)
        nuevo_libro.siguiente = self.cabeza
        self.cabeza = nuevo_libro
        self.pila_acciones.apilar(f"Libro agregado: {titulo}")

    def cargar_libros(self, nombre_archivo):
        if not os.path.exists(nombre_archivo):
            raise RuntimeError("No se pudo abrir el archivo")
        
        with open(nombre_archivo, 'r') as archivo:
            for linea in archivo:
                datos = linea.strip().split(',')
                if len(datos) < 6:
                    continue

                titulo, autor, año, editorial, isbn, paginas = datos

                if "a.C." in año:
                    año = -int(año.replace(" a.C.", ""))  # Convertir a número negativo
                else:
                    año = int(año)

                self.agregar_libro(titulo, autor, año, editorial, isbn, int(paginas))

    # Métodos de ordenamiento
    def ordenar_libros(self, metodo="quicksort"):
        """Ordena los libros por título usando el método especificado"""
        if metodo == "quicksort":
            self.cabeza = self._quicksort(self.cabeza)
        elif metodo == "mergesort":
            self.cabeza = self._mergesort(self.cabeza)

    def _quicksort(self, inicio):
        if not inicio or not inicio.siguiente:
            return inicio

        # Implementación del quicksort para lista enlazada
        pivot = inicio
        menores = mayores = None

        actual = inicio.siguiente
        while actual:
            siguiente = actual.siguiente
            if actual.titulo < pivot.titulo:
                actual.siguiente = menores
                menores = actual
            else:
                actual.siguiente = mayores
                mayores = actual
            actual = siguiente

        menores = self._quicksort(menores)
        mayores = self._quicksort(mayores)

        if menores:
            temp = menores
            while temp.siguiente:
                temp = temp.siguiente
            temp.siguiente = pivot
        else:
            menores = pivot
        pivot.siguiente = mayores

        return menores

    # Métodos de búsqueda
    def buscar_libro(self, criterio, valor):
        """Búsqueda de libros por diferentes criterios"""
        resultados = []
        actual = self.cabeza

        while actual:
            if criterio == "titulo" and valor.lower() in actual.titulo.lower():
                resultados.append(actual)
            elif criterio == "autor" and valor.lower() in actual.autor.lower():
                resultados.append(actual)
            elif criterio == "isbn" and valor == actual.isbn:
                resultados.append(actual)
            actual = actual.siguiente

        return resultados

    def solicitar_libro(self, nombre, dni, titulo_libro):
        if not self.esta_disponible(titulo_libro):
            print("Libro no disponible. Agregando a la cola de espera.")
            self.cola_espera.encolar(nombre, dni, titulo_libro)
            return

        try:
            if not self._validar_dni(dni):
                raise ValueError("DNI inválido")

            if (nombre, dni) not in self.solicitudes:
                self.solicitudes[(nombre, dni)] = []
            
            self.solicitudes[(nombre, dni)].append(titulo_libro)
            self.pila_acciones.apilar(
                f"Libro solicitado: {titulo_libro} por {nombre}",
                {"tipo": "solicitud", "nombre": nombre, "dni": dni, "titulo": titulo_libro}
            )
            self.actualizar_archivo()
        except Exception as e:
            raise RuntimeError(f"Error al solicitar libro: {str(e)}")

    def devolver_libro(self, nombre, dni, titulo_libro):
        if (nombre, dni) in self.solicitudes and titulo_libro in self.solicitudes[(nombre, dni)]:
            self.solicitudes[(nombre, dni)].remove(titulo_libro)
            if not self.solicitudes[(nombre, dni)]:
                del self.solicitudes[(nombre, dni)]
            
            # Verificar si hay solicitudes en espera
            if not self.cola_espera.esta_vacia():
                siguiente_solicitud = self.cola_espera.desencolar()
                if siguiente_solicitud:
                    self.solicitar_libro(*siguiente_solicitud)
                    print(f"Libro asignado al siguiente lector en la cola: {siguiente_solicitud[0]}")

            self.pila_acciones.apilar(
                f"Libro devuelto: {titulo_libro}",
                {"tipo": "devolucion", "nombre": nombre, "dni": dni, "titulo": titulo_libro}
            )
            self.agregar_libro_al_archivo(titulo_libro)

    def deshacer_ultima_accion(self):
        """Deshace la última acción realizada"""
        accion, estado_anterior = self.pila_acciones.desapilar()
        if estado_anterior:
            if estado_anterior["tipo"] == "solicitud":
                self.cancelar_solicitud(
                    estado_anterior["nombre"],
                    estado_anterior["dni"],
                    estado_anterior["titulo"]
                )
            elif estado_anterior["tipo"] == "devolucion":
                self.solicitar_libro(
                    estado_anterior["nombre"],
                    estado_anterior["dni"],
                    estado_anterior["titulo"]
                )
        return accion

    def guardar_solicitudes(self, nombre_archivo="solicitudes.txt"):
        """Guarda las solicitudes actuales en un archivo"""
        with open(nombre_archivo, 'w') as archivo:
            for (nombre, dni), libros in self.solicitudes.items():
                for libro in libros:
                    archivo.write(f"{nombre},{dni},{libro}\n")

    def cargar_solicitudes(self, nombre_archivo="solicitudes.txt"):
        """Carga las solicitudes desde un archivo"""
        if os.path.exists(nombre_archivo):
            with open(nombre_archivo, 'r') as archivo:
                for linea in archivo:
                    nombre, dni, libro = linea.strip().split(',')
                    self.solicitar_libro(nombre, dni, libro)

    @staticmethod
    def _validar_dni(dni):
        """Valida el formato del DNI"""
        return bool(re.match(r'^\d{8}[A-Z]$', dni))

def main():
    biblioteca = Biblioteca()

    try:
        biblioteca.cargar_libros("biblioteca.txt")
        biblioteca.cargar_solicitudes("solicitudes.txt")
    except RuntimeError as e:
        print(f"Error al cargar datos: {e}")

    while True:
        print("\nSistema de Gestión de Biblioteca")
        print("1. Mostrar todos los libros")
        print("2. Solicitar un libro")
        print("3. Devolver un libro")
        print("4. Buscar libro")
        print("5. Ordenar libros")
        print("6. Agregar nuevo libro")
        print("7. Deshacer última acción")
        print("8. Guardar datos")
        print("9. Ver cola de espera")
        print("10. Salir")
        opcion = input("Elige una opción: ")

        if opcion == '1':
            biblioteca.mostrar_libros()
        
        elif opcion == '2':
            try:
                nombre = input("Ingresa el nombre del lector: ")
                dni = input("Ingresa el DNI (8 números y 1 letra mayúscula): ")
                titulo_libro = input("Ingresa el título del libro: ")
                biblioteca.solicitar_libro(nombre, dni, titulo_libro)
                print("Libro solicitado con éxito.")
            except RuntimeError as e:
                print(f"Error al solicitar el libro: {e}")
            except ValueError as e:
                print(f"Error de validación: {e}")
        
        elif opcion == '3':
            nombre = input("Ingresa el nombre del lector: ")
            dni = input("Ingresa el DNI: ")
            if (nombre, dni) in biblioteca.solicitudes:
                print("Libros solicitados:")
                for idx, titulo in enumerate(biblioteca.solicitudes[(nombre, dni)], start=1):
                    print(f"{idx}. {titulo}")
                try:
                    titulo_libro = input("Ingresa el número del libro a devolver: ")
                    libro_a_devolver = biblioteca.solicitudes[(nombre, dni)][int(titulo_libro) - 1]
                    biblioteca.devolver_libro(nombre, dni, libro_a_devolver)
                except (IndexError, ValueError):
                    print("Número de libro inválido.")
            else:
                print("No tienes libros solicitados.")
        
        elif opcion == '4':
            print("\nOpciones de búsqueda:")
            print("1. Por título")
            print("2. Por autor")
            print("3. Por ISBN")
            sub_opcion = input("Elige un criterio de búsqueda: ")
            
            criterios = {
                '1': 'titulo',
                '2': 'autor',
                '3': 'isbn'
            }
            
            if sub_opcion in criterios:
                valor = input(f"Ingresa el {criterios[sub_opcion]} a buscar: ")
                resultados = biblioteca.buscar_libro(criterios[sub_opcion], valor)
                if resultados:
                    print("\nLibros encontrados:")
                    for libro in resultados:
                        print(f"Título: {libro.titulo}")
                        print(f"Autor: {libro.autor}")
                        print(f"ISBN: {libro.isbn}")
                        print(f"Editorial: {libro.editorial}")
                        print(f"Año: {libro.año}")
                        print(f"Páginas: {libro.paginas}")
                        print("-" * 30)
                else:
                    print("No se encontraron libros con ese criterio.")
            else:
                print("Opción inválida.")
        
        elif opcion == '5':
            print("\nMétodos de ordenamiento:")
            print("1. QuickSort")
            print("2. MergeSort")
            metodo = input("Elige el método de ordenamiento: ")
            
            if metodo == '1':
                biblioteca.ordenar_libros("quicksort")
            elif metodo == '2':
                biblioteca.ordenar_libros("mergesort")
            else:
                print("Método de ordenamiento no válido.")
            print("Libros ordenados.")
        
        elif opcion == '6':
            try:
                print("\nAgregar nuevo libro:")
                titulo = input("Título del libro: ")
                autor = input("Autor del libro: ")
                año = input("Año de edición: ")
                editorial = input("Editorial: ")
                isbn = input("ISBN (13 dígitos): ")
                paginas = input("Número de páginas: ")
                
                nuevo_libro = Libro(titulo, autor, int(año), editorial, isbn, int(paginas))
                if nuevo_libro.validar_isbn():
                    biblioteca.agregar_libro(titulo, autor, int(año), editorial, isbn, int(paginas))
                    print("Libro agregado con éxito.")
                else:
                    print("ISBN inválido. El libro no fue agregado.")
            except ValueError as e:
                print(f"Error al agregar el libro: {e}")
        
        elif opcion == '7':
            try:
                accion = biblioteca.deshacer_ultima_accion()
                print(f"Acción deshecha: {accion}")
            except Exception as e:
                print(f"Error al deshacer la acción: {e}")
        
        elif opcion == '8':
            try:
                biblioteca.guardar_datos("biblioteca.txt")
                biblioteca.guardar_solicitudes("solicitudes.txt")
                print("Datos guardados exitosamente.")
            except Exception as e:
                print(f"Error al guardar los datos: {e}")
        
        elif opcion == '9':
            if biblioteca.cola_espera.esta_vacia():
                print("No hay solicitudes en la cola de espera.")
            else:
                print("\nCola de espera actual:")
                cola_temp = biblioteca.cola_espera.cola.copy()
                for i, (nombre, dni, titulo) in enumerate(cola_temp, 1):
                    print(f"{i}. Lector: {nombre} (DNI: {dni}) - Libro: {titulo}")
        
        elif opcion == '10':
            print("Guardando datos antes de salir...")
            try:
                biblioteca.guardar_datos("biblioteca.txt")
                biblioteca.guardar_solicitudes("solicitudes.txt")
                print("¡Hasta luego!")
                break
            except Exception as e:
                print(f"Error al guardar los datos: {e}")
                print("¡Hasta luego!")
                break
        
        else:
            print("Opción inválida. Por favor, intenta de nuevo.")

if __name__ == "__main__":
    main()