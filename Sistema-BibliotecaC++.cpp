#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <queue>
#include <stack>
#include <stdexcept>

using namespace std;

// Estructura de libro
struct Book {
    string title;
    string author;
    int year;
    string publisher;
    string isbn;
    int pages;
    Book* next;

    Book(string t, string a, int y, string p, string i, int pg) 
        : title(t), author(a), year(y), publisher(p), isbn(i), pages(pg), next(nullptr) {}
};

// Estructura de solicitud de lector
struct ReaderRequest {
    string name;
    string dni;
    string bookTitle;
};

// Nodo para la cola
class QueueNode {
public:
    ReaderRequest request;
    QueueNode* next;

    QueueNode(const ReaderRequest& req) : request(req), next(nullptr) {}
};

// Cola para solicitudes de lectores
class RequestQueue {
private:
    QueueNode* front;
    QueueNode* rear;

public:
    RequestQueue() : front(nullptr), rear(nullptr) {}

    void enqueue(const ReaderRequest& req) {
        QueueNode* newNode = new QueueNode(req);
        if (rear) {
            rear->next = newNode;
        } else {
            front = newNode;
        }
        rear = newNode;
    }

    ReaderRequest dequeue() {
        if (!front) throw runtime_error("La cola está vacía");
        QueueNode* temp = front;
        ReaderRequest req = front->request;
        front = front->next;
        if (!front) rear = nullptr;
        delete temp;
        return req;
    }

    bool isEmpty() const {
        return front == nullptr;
    }
};

// Pila de acciones
class ActionStack {
private:
    stack<string> actions;

public:
    void push(const string& action) {
        actions.push(action);
    }

    string pop() {
        if (actions.empty()) throw runtime_error("La pila está vacía");
        string action = actions.top();
        actions.pop();
        return action;
    }

    bool isEmpty() const {
        return actions.empty();
    }
};

// Sistema de gestión de biblioteca
class Library {
private:
    Book* head;
    RequestQueue requestQueue;
    ActionStack actionStack;

public:
    Library() : head(nullptr) {}

    // Cargar libros desde un archivo
    void loadBooks(const string& filename) {
        ifstream file(filename);
        if (!file.is_open()) throw runtime_error("No se pudo abrir el archivo");

        string line;
        while (getline(file, line)) {
            stringstream ss(line);
            string title, author, publisher, isbn;
            int year, pages;
            getline(ss, title, ',');
            getline(ss, author, ',');
            ss >> year;
            ss.ignore();
            getline(ss, publisher, ',');
            getline(ss, isbn, ',');
            ss >> pages;

            addBook(title, author, year, publisher, isbn, pages);
        }
        file.close();
    }

    // Agregar un nuevo libro
    void addBook(const string& title, const string& author, int year, const string& publisher, const string& isbn, int pages) {
        Book* newBook = new Book(title, author, year, publisher, isbn, pages);
        newBook->next = head;
        head = newBook;
        actionStack.push("Libro agregado: " + title);
    }

    // Solicitar un libro
    void requestBook(const string& name, const string& dni, const string& bookTitle) {
        // Verificar si el libro existe
        Book* current = head;
        while (current) {
            if (current->title == bookTitle) {
                ReaderRequest req = {name, dni, bookTitle};
                requestQueue.enqueue(req);
                actionStack.push("Libro solicitado: " + bookTitle + " por " + name);
                return;
            }
            current = current->next;
        }
        throw runtime_error("Libro no encontrado: " + bookTitle);
    }

    // Devolver un libro
    void returnBook() {
        if (!requestQueue.isEmpty()) {
            ReaderRequest req = requestQueue.dequeue();
            cout << req.name << " devolvió el libro: " << req.bookTitle << endl;
            actionStack.push("Libro devuelto: " + req.bookTitle + " por " + req.name);
        } else {
            cout << "No hay solicitudes en la cola." << endl;
        }
    }

    // Guardar libros y solicitudes en archivos
    void saveData(const string& booksFile, const string& requestsFile) {
        ofstream booksOut(booksFile);
        if (!booksOut.is_open()) throw runtime_error("No se pudo abrir el archivo de libros para escribir");

        Book* current = head;
        while (current) {
            booksOut << current->title << "," << current->author << "," 
                      << current->year << "," << current->publisher << "," 
                      << current->isbn << "," << current->pages << endl;
            current = current->next;
        }
        booksOut.close();

        // Guardar solicitudes no está implementado en este ejemplo
        // Puedes implementarlo de forma similar iterando en la cola
    }

    // Mostrar todos los libros
    void displayBooks() {
        Book* current = head;
        while (current) {
            cout << "Título: " << current->title << ", Autor: " << current->author 
                 << ", Año: " << current->year << ", Editorial: " << current->publisher 
                 << ", ISBN: " << current->isbn << ", Páginas: " << current->pages << endl;
            current = current->next;
        }
    }

    // Destructor para liberar memoria
    ~Library() {
        while (head) {
            Book* temp = head;
            head = head->next;
            delete temp;
        }
    }
};

// Función principal para ejecutar el sistema de gestión de biblioteca
int main() {
    Library library;

    // Cargar datos iniciales
    try {
        library.loadBooks("biblioteca.txt");
    } catch (const runtime_error& e) {
        cerr << "Error al cargar los libros: " << e.what() << endl;
    }

    // Interfaz de comandos simple
    while (true) {
        cout << "\nSistema de Gestión de Biblioteca\n";
        cout << "1. Mostrar todos los libros\n";
        cout << "2. Solicitar un libro\n";
        cout << "3. Devolver un libro\n";
        cout << "4. Guardar datos\n";
        cout << "5. Salir\n";
        cout << "Elija una opción: ";
        int choice;
        cin >> choice;

        if (choice == 1) {
            library.displayBooks();
        } else if (choice == 2) {
            string name, dni, bookTitle;
            cout << "Ingrese el nombre del lector: ";
            cin.ignore();
            getline(cin, name);
            cout << "Ingrese el DNI: ";
            getline(cin, dni);
            cout << "Ingrese el título del libro: ";
            getline(cin, bookTitle);

            try {
                library.requestBook(name, dni, bookTitle);
                cout << "Libro solicitado con éxito." << endl;
            } catch (const runtime_error& e) {
                cerr << "Error al solicitar el libro: " << e.what() << endl;
            }
        } else if (choice == 3) {
            library.returnBook();
        } else if (choice == 4) {
            try {
                library.saveData("biblioteca.txt", "solicitudes.txt");
                cout << "Datos guardados con éxito." << endl;
            } catch (const runtime_error& e) {
                cerr << "Error al guardar los datos: " << e.what() << endl;
            }
        } else if (choice == 5) {
            break;
        } else {
            cout << "Opción inválida. Por favor, intente nuevamente." << endl;
        }
    }

    return 0;
}
