// ====================================================================
// CONFIGURACIÓN SEGURA
// ====================================================================
const API_BASE_URL = "http://127.0.0.1:5000/api"
const AUTH_URL = `${API_BASE_URL}/auth`
const INVENTARIO_URL = `${API_BASE_URL}/inventario`

// ====================================================================
// ELEMENTOS DEL DOM
// ====================================================================
const loginContainer = document.getElementById("loginContainer")
const dashboard = document.getElementById("dashboard")
const loginForm = document.getElementById("loginForm")
const loginError = document.getElementById("loginError")
const logoutBtn = document.getElementById("logoutBtn")
const userName = document.getElementById("userName")
const userInitial = document.getElementById("userInitial")

const inventoryTableBody = document.getElementById("inventoryTableBody")
const totalItems = document.getElementById("totalItems")
const lowStockItems = document.getElementById("lowStockItems")
const totalValue = document.getElementById("totalValue")

// Elementos para seriales
const componentTypeSelect = document.getElementById("componentType")
const serialProductSelect = document.getElementById("serialProduct")
const serialCode = document.getElementById("serialCode")
const serialForm = document.getElementById("serialForm")
const serialMessage = document.getElementById("serialMessage")

// Elementos para productos
const addProductBtn = document.getElementById("addProductBtn")
const productModal = document.getElementById("productModal")
const closeProductModal = document.getElementById("closeProductModal")
const productForm = document.getElementById("productForm")
const productMessage = document.getElementById("productMessage")
const productTypeSelect = document.getElementById("productType")

// Elementos comunes
const addItemBtn = document.getElementById("addItemBtn")
const itemModal = document.getElementById("itemModal")
const closeModal = document.getElementById("closeModal")
const searchInput = document.getElementById("searchInput")
const searchBtn = document.getElementById("searchBtn")

const serialsDetailModal = document.getElementById("serialsDetailModal")
const closeSerialsModal = document.getElementById("closeSerialsModal")
const serialsModalTitle = document.getElementById("serialsModalTitle")
const serialsTableBody = document.getElementById("serialsTableBody")

// ====================================================================
// VARIABLES GLOBALES OPTIMIZADAS
// ====================================================================
let currentUser = null
let ALL_PRODUCT_MODELS = []
let productTypesCache = null
let inventoryCache = null
let sessionCheckerInterval = null

// ====================================================================
// MANEJO SEGURO DE AUTENTICACIÓN
// ====================================================================

/**
 * Login seguro
 */
async function secureLogin(username, password) {
    try {
        const response = await fetch(`${AUTH_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            currentUser = result.user;
            userInitial.textContent = currentUser.name.charAt(0);
            userName.textContent = currentUser.name;

            loginContainer.style.display = "none";
            dashboard.style.display = "block";
            loginError.style.display = "none";

            loadInventoryData();
            loadComponentTypes();
            
            startSessionChecker();
        } else {
            showLoginError(result.error);
        }
    } catch (error) {
        console.error("Error de login:", error);
        showLoginError("Error de conexión con el servidor");
    }
}

/**
 * Verificar sesión activa
 */
async function checkSession() {
    try {
        const response = await fetch(`${AUTH_URL}/check`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
                currentUser = data.user;
                return true;
            }
        }
    } catch (error) {
        console.error("Error verificando sesión:", error);
    }
    
    return false;
}

/**
 * Logout seguro
 */
async function secureLogout() {
    try {
        await fetch(`${AUTH_URL}/logout`, {
            method: "POST",
            credentials: 'include'
        });
    } catch (error) {
        console.error("Error en logout:", error);
    } finally {
        currentUser = null;
        ALL_PRODUCT_MODELS = [];
        productTypesCache = null;
        inventoryCache = null;
        
        dashboard.style.display = "none";
        loginContainer.style.display = "flex";
        loginForm.reset();
        loginError.style.display = "none";
        
        stopSessionChecker();
    }
}

/**
 * Verificador periódico de sesión
 */
function startSessionChecker() {
    sessionCheckerInterval = setInterval(async () => {
        const isValid = await checkSession();
        if (!isValid && currentUser) {
            alert("Sesión expirada. Por favor ingresa nuevamente.");
            secureLogout();
        }
    }, 5 * 60 * 1000); // 5 minutos
}

function stopSessionChecker() {
    if (sessionCheckerInterval) {
        clearInterval(sessionCheckerInterval);
        sessionCheckerInterval = null;
    }
}

/**
 * Fetch seguro con manejo de autenticación
 */
async function secureFetch(url, options = {}) {
    const config = {
        ...options,
        credentials: 'include'
    };
    
    const response = await fetch(url, config);
    
    if (response.status === 401) {
        secureLogout();
        throw new Error("Sesión expirada");
    }
    
    return response;
}

// ====================================================================
// AUTENTICACIÓN - EVENT LISTENERS
// ====================================================================

loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
    secureLogin(username, password);
});

logoutBtn.addEventListener("click", secureLogout);

function showLoginError(message) {
    loginError.textContent = message;
    loginError.style.display = "block";
}

// ====================================================================
// GESTIÓN DE INVENTARIO - OPTIMIZADO Y SEGURO
// ====================================================================

/**
 * Carga el inventario desde la base de datos con caché
 */
async function loadInventoryData(filter = "") {
    try {
        const response = await secureFetch(`${INVENTARIO_URL}/stock`);

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        let data = await response.json();
        
        inventoryCache = data;
        renderInventoryTable(data, filter);

    } catch (error) {
        if (error.message === "Sesión expirada") {
            showLoginError("Sesión expirada");
        } else {
            console.error("Error al cargar inventario:", error);
            showInventoryError();
        }
    }
}

/**
 * Renderiza la tabla de inventario
 */
function renderInventoryTable(data, filter = "") {
    if (filter) {
        const lowerFilter = filter.toLowerCase();
        data = data.filter(item =>
            item.producto.toLowerCase().includes(lowerFilter) || 
            item.codigo_sku.toLowerCase().includes(lowerFilter)
        );
    }

    inventoryTableBody.innerHTML = "";
    let totalSeriales = 0;
    let lowStockCount = 0;

    if (data.length === 0) {
        inventoryTableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px;">
                    No se encontraron productos que coincidan con la búsqueda.
                </td>
            </tr>
        `;
        updateStatistics(0, 0, 0);
        return;
    }

    data.forEach((item) => {
        const row = document.createElement("tr");
        const stockStatus = item.stock_disponible <= 5 ? "Bajo" : "Normal";
        const statusClass = item.stock_disponible <= 5 ? "danger" : "success";
        
        const historialDesc = item.ultima_actividad_desc || "No hay registro";
        const historialClass = "btn-history-link";

        totalSeriales += item.stock_disponible;
        if (item.stock_disponible <= 5) lowStockCount++;

        row.innerHTML = `
            <td>${item.producto_id}</td>
            <td>${item.producto}</td>
            <td>${item.tipo_pieza}</td>
            <td>${item.codigo_sku}</td>
            <td class="stock-cell">
                <button class="btn-stock" data-id="${item.producto_id}" data-name="${item.producto}">
                    ${item.stock_disponible} <i class="fas fa-eye"></i>
                </button>
            </td>
            <td><span class="badge badge-${statusClass}">${stockStatus}</span></td>
            <td>
                <span class="${historialClass}" data-id="${item.producto_id}" data-name="${item.producto}">
                    ${historialDesc}
                </span>
            </td>
        `;

        inventoryTableBody.appendChild(row);
    });

    updateStatistics(data.length, lowStockCount, totalSeriales);
    attachStockButtonEvents();
}

/**
 * Muestra error en la tabla de inventario
 */
function showInventoryError() {
    inventoryTableBody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align: center; color: #c33; padding: 40px;">
                ❌ Error al conectar con el servidor.
            </td>
        </tr>
    `;
}

/**
 * Asigna eventos a los botones de stock
 */
function attachStockButtonEvents() {
    document.querySelectorAll(".btn-stock").forEach((btn) => {
        btn.addEventListener("click", function () {
            const id = Number.parseInt(this.getAttribute("data-id"));
            const name = this.getAttribute("data-name");
            showSerialsDetail(id, name);
        });
    });
}

// ====================================================================
// GESTIÓN DE SERIALES - SEGURO
// ====================================================================

/**
 * Carga la lista de TIPOS DE PIEZA para el primer select del modal
 */
async function loadComponentTypes() {
    try {
        if (productTypesCache) {
            populateComponentTypes(productTypesCache);
            return;
        }

        const response = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

        const types = await response.json();
        productTypesCache = types;
        
        populateComponentTypes(types);
        await fetchAllProductModels();

    } catch (error) {
        console.error("Error al cargar tipos de pieza:", error);
        componentTypeSelect.innerHTML = '<option value="">Error al cargar Tipos</option>';
    }
}

/**
 * Llena el select de tipos de componente
 */
function populateComponentTypes(types) {
    componentTypeSelect.innerHTML = '<option value="">-- Selecciona un Tipo --</option>';
    types.forEach((t) => {
        const option = document.createElement("option");
        option.value = t.tipo_id;
        option.textContent = t.tipo_modelo;
        componentTypeSelect.appendChild(option);
    });
}

/**
 * Carga todos los modelos para filtrar localmente
 */
async function fetchAllProductModels() {
    try {
        const response = await secureFetch(`${INVENTARIO_URL}/productos`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
        
        ALL_PRODUCT_MODELS = await response.json();
    } catch (error) {
        console.error("Error al cargar todos los modelos:", error);
        serialProductSelect.innerHTML = '<option value="">Error al cargar Modelos</option>';
    }
}

/**
 * Filtra y llena el segundo desplegable (MODELO ESPECÍFICO)
 */
function filterProductModels() {
    const selectedTypeId = parseInt(componentTypeSelect.value);
    
    if (!selectedTypeId) {
        serialProductSelect.innerHTML = '<option value="">-- Selecciona un Modelo (Selecciona Tipo primero) --</option>';
        serialProductSelect.disabled = true;
        return;
    }

    serialProductSelect.innerHTML = '<option value="">-- Selecciona un Modelo Específico --</option>';
    const filteredModels = ALL_PRODUCT_MODELS.filter(model => model.tipo_pieza_id === selectedTypeId);

    if (filteredModels.length === 0) {
        serialProductSelect.innerHTML = '<option value="">-- No hay modelos para este tipo --</option>';
    } else {
        filteredModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.producto_id;
            option.textContent = `${model.nombre} (SKU: ${model.codigo_sku})`;
            serialProductSelect.appendChild(option);
        });
    }

    serialProductSelect.disabled = false;
}

/**
 * Muestra el detalle de seriales de un producto
 */
async function showSerialsDetail(productoId, productoNombre) {
    serialsModalTitle.textContent = `Seriales en Almacén para: ${productoNombre}`;
    serialsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;"><div class="loading"></div> Cargando seriales...</td></tr>';
    serialsDetailModal.style.display = "flex";

    try {
        const response = await secureFetch(`${INVENTARIO_URL}/seriales/${productoId}`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

        const serials = await response.json();
        renderSerialsTable(serials);

    } catch (error) {
        console.error("Error al cargar seriales:", error);
        serialsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #c33;">Error al obtener seriales</td></tr>';
    }
}

/**
 * Renderiza la tabla de seriales
 */
function renderSerialsTable(serials) {
    serialsTableBody.innerHTML = "";

    if (serials.length === 0) {
        serialsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No hay seriales en ALMACEN para este modelo.</td></tr>';
        return;
    }

    serials.forEach((s) => {
        const row = serialsTableBody.insertRow();
        row.insertCell().textContent = s.serial_id;
        row.insertCell().textContent = s.codigo_unico_serial;

        const statusCell = row.insertCell();
        const statusClass = s.estado === 'ALMACEN' ? 'success' : s.estado === 'DAÑADO' ? 'danger' : 'warning';
        statusCell.innerHTML = `<span class="badge badge-${statusClass}">${s.estado}</span>`;

        row.insertCell().textContent = s.ultima_actividad || 'N/A';
        
        const actionCell = row.insertCell();
        actionCell.innerHTML = `<button class="action-btn view-history-btn" data-serial-id="${s.serial_id}" title="Ver historial completo">
            <i class="fas fa-history"></i>
        </button>`;
    });

    attachHistoryButtonEvents();
}

/**
 * Asigna eventos a los botones de historial
 */
function attachHistoryButtonEvents() {
    document.querySelectorAll(".view-history-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            const serialId = this.getAttribute("data-serial-id");
            showSerialHistory(serialId);
        });
    });
}

/**
 * Muestra el historial completo de un serial
 */
async function showSerialHistory(serialId) {
    alert(`📋 Historial del Serial ID: ${serialId}\n\nEsta funcionalidad estará disponible en la próxima versión.`);
}

/**
 * Registra un nuevo serial en la base de datos
 */
serialForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    serialMessage.style.display = "none";

    if (!componentTypeSelect.value || !serialProductSelect.value) {
        showMessage(serialMessage, "❌ Por favor selecciona tanto el Tipo como el Modelo", "danger");
        return;
    }

    const newSerial = {
        producto_id: Number.parseInt(serialProductSelect.value),
        codigo_unico_serial: serialCode.value.trim(),
    };

    if (!newSerial.codigo_unico_serial) {
        showMessage(serialMessage, "❌ Por favor ingresa un código de serial", "danger");
        return;
    }

    try {
        const response = await secureFetch(`${INVENTARIO_URL}/serial`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newSerial),
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(serialMessage, `✅ ${result.mensaje}`, "success");
            serialForm.reset();
            inventoryCache = null;
            loadInventoryData();
            setTimeout(() => {
                itemModal.style.display = "none";
                serialMessage.style.display = "none";
            }, 2000);
        } else {
            showMessage(serialMessage, `❌ ${result.error}`, "danger");
        }
    } catch (error) {
        console.error("Error al registrar serial:", error);
        showMessage(serialMessage, "❌ Error de conexión con el servidor", "danger");
    }
});

// ====================================================================
// GESTIÓN DE PRODUCTOS - SEGURO
// ====================================================================

/**
 * Abre el modal para agregar nuevo producto
 */
addProductBtn.addEventListener("click", () => {
    productModal.style.display = "flex";
    productForm.reset();
    productMessage.style.display = "none";
    loadProductTypes();
});

/**
 * Carga los tipos de pieza para el modal de productos
 */
async function loadProductTypes() {
    try {
        if (productTypesCache) {
            populateProductTypes(productTypesCache);
            return;
        }

        const response = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
        if (!response.ok) throw new Error('Error al cargar tipos');
        
        const types = await response.json();
        productTypesCache = types;
        populateProductTypes(types);
        
    } catch (error) {
        console.error("Error al cargar tipos para producto:", error);
        productTypeSelect.innerHTML = '<option value="">Error al cargar tipos</option>';
    }
}

/**
 * Llena el select de tipos para productos
 */
function populateProductTypes(types) {
    productTypeSelect.innerHTML = '<option value="">-- Selecciona un Tipo --</option>';
    types.forEach((t) => {
        const option = document.createElement("option");
        option.value = t.tipo_id;
        option.textContent = t.tipo_modelo;
        productTypeSelect.appendChild(option);
    });
}

/**
 * Registra un nuevo producto en la base de datos
 */
productForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    productMessage.style.display = "none";

    const newProduct = {
        nombre: document.getElementById("productName").value.trim(),
        descripcion: document.getElementById("productDescription").value.trim(),
        tipo_pieza_id: parseInt(productTypeSelect.value),
        codigo_sku: document.getElementById("productSKU").value.trim()
    };

    if (!newProduct.nombre || !newProduct.tipo_pieza_id || !newProduct.codigo_sku) {
        showMessage(productMessage, "❌ Por favor completa todos los campos requeridos", "danger");
        return;
    }

    try {
        const response = await secureFetch(`${INVENTARIO_URL}/productos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newProduct),
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(productMessage, `✅ ${result.mensaje}`, "success");
            productForm.reset();
            
            ALL_PRODUCT_MODELS = [];
            inventoryCache = null;
            await fetchAllProductModels();
            loadInventoryData();
            
            setTimeout(() => {
                productModal.style.display = "none";
                productMessage.style.display = "none";
            }, 2000);
        } else {
            showMessage(productMessage, `❌ ${result.error}`, "danger");
        }
    } catch (error) {
        console.error("Error al registrar producto:", error);
        showMessage(productMessage, "❌ Error de conexión con el servidor", "danger");
    }
});

// ====================================================================
// FUNCIONES AUXILIARES
// ====================================================================

function updateStatistics(totalModelos, lowStockCount, totalSeriales) {
    totalItems.textContent = totalModelos;
    lowStockItems.textContent = lowStockCount;
    totalValue.textContent = totalSeriales;
}

function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `alert alert-${type}`;
    element.style.display = "block";
}

// ====================================================================
// EVENTOS DE MODALES Y BÚSQUEDA
// ====================================================================

addItemBtn.addEventListener("click", () => {
    itemModal.style.display = "flex";
    serialForm.reset();
    serialMessage.style.display = "none";
    componentTypeSelect.innerHTML = '<option value="">-- Selecciona un Tipo --</option>';
    serialProductSelect.innerHTML = '<option value="">-- Selecciona un Modelo (Selecciona Tipo primero) --</option>';
    serialProductSelect.disabled = true;
    loadComponentTypes();
});

componentTypeSelect.addEventListener('change', filterProductModels);

closeModal.addEventListener("click", () => {
    itemModal.style.display = "none";
});

closeProductModal.addEventListener("click", () => {
    productModal.style.display = "none";
});

closeSerialsModal.addEventListener("click", () => {
    serialsDetailModal.style.display = "none";
});

window.addEventListener("click", (e) => {
    if (e.target === itemModal) itemModal.style.display = "none";
    if (e.target === productModal) productModal.style.display = "none";
    if (e.target === serialsDetailModal) serialsDetailModal.style.display = "none";
});

searchBtn.addEventListener("click", () => {
    loadInventoryData(searchInput.value);
});

searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
        loadInventoryData(searchInput.value);
    }
});

searchInput.addEventListener("input", (e) => {
    if (e.target.value === "") {
        loadInventoryData("");
    }
});

// ====================================================================
// INICIALIZACIÓN SEGURA
// ====================================================================
document.addEventListener("DOMContentLoaded", async () => {
    const hasSession = await checkSession();
    
    if (hasSession) {
        loginContainer.style.display = "none";
        dashboard.style.display = "block";
        loadInventoryData();
        loadComponentTypes();
    } else {
        loginContainer.style.display = "flex";
        dashboard.style.display = "none";
    }
    
    console.log("✅ Sistema de inventario seguro inicializado");
});