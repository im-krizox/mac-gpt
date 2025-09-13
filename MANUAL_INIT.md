# 🚀 Inicialización Manual de Datos - MAC-GPT

## 📋 Situación Actual
El chatbot está deployado pero necesita procesar los datos iniciales para funcionar.

## 🔧 Pasos para Inicializar

### **1. Agregar Variable de Administrador**

En tu **Render Dashboard**:
1. Ve a tu servicio → **Environment**
2. **Add Environment Variable**:
   ```
   Key: ADMIN_KEY
   Value: MAC_Admin_2024_SecureKey
   ```
3. **Save Changes** (esto hará redeploy automático, espera 2-3 minutos)

### **2. Ejecutar Comando de Inicialización**

**Opción A - Terminal/CMD (una sola línea):**
```bash
curl -X POST https://tu-app-name.onrender.com/api/admin/update-data -H "Content-Type: application/json" -d "{\"admin_key\": \"MAC_Admin_2024_SecureKey\"}"
```

**Opción B - PowerShell (Windows):**
```powershell
Invoke-RestMethod -Uri "https://tu-app-name.onrender.com/api/admin/update-data" -Method POST -ContentType "application/json" -Body '{"admin_key": "MAC_Admin_2024_SecureKey"}'
```

**Opción C - Postman/Insomnia:**
- **Method**: POST
- **URL**: `https://tu-app-name.onrender.com/api/admin/update-data`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "admin_key": "MAC_Admin_2024_SecureKey"
  }
  ```

### **3. Monitorear Progreso**

**Verificar que inició:**
```bash
curl https://tu-app-name.onrender.com/api/admin/pipeline-status
```

**Verificar cuando termine:**
```bash
curl https://tu-app-name.onrender.com/api/status
```

### **4. Respuestas Esperadas**

**Al ejecutar el comando inicial:**
```json
{
  "success": true,
  "message": "Pipeline ETL iniciado. Los datos se actualizarán en unos minutos."
}
```

**Cuando esté listo (después de 8-12 minutos):**
```json
{
  "api_configured": true,
  "data_exists": true,
  "status": "ready"
}
```

## ⏱️ Tiempo Estimado

- **Iniciar comando**: Inmediato
- **Procesamiento completo**: 8-12 minutos
- **Chatbot funcional**: Al completar el procesamiento

## 🔍 Solución de Problemas

### Si obtienes error 403:
- Verificar que `ADMIN_KEY` esté configurada correctamente en Render
- Usar exactamente la misma clave en el comando

### Si obtienes error 409:
- El pipeline ya está ejecutándose
- Esperar a que termine (~10 minutos)

### Si obtienes error de conexión:
- Verificar que la URL de tu app esté correcta
- Reemplazar `tu-app-name` con tu nombre real de Render

## ✅ Verificación Final

Una vez que `/api/status` devuelva `"status": "ready"`, tu chatbot estará completamente funcional.

---

**💡 Tip**: Guarda el comando para futuras actualizaciones de datos (recomendado mensualmente).
