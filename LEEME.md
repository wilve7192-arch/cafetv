# CaféTV — App de TV con la lista de iptv-org (GitHub)

```
web/      → la app (index.html). Es la misma interfaz para todo.
android/  → proyecto Android para Fire TV (usa web/index.html)
tizen/    → proyecto para Samsung TV (Tizen)
.github/workflows/build-apk.yml → GitHub crea el APK automáticamente
```

## 1. Fire TV (APK)

**Crear el APK sin instalar nada (con GitHub):**
1. Crea un repositorio nuevo en github.com (puede ser privado).
2. Sube TODO el contenido de esta carpeta, incluida la carpeta oculta `.github`
   ("Add file → Upload files" y arrastra las carpetas).
3. Ve a la pestaña **Actions** → "Crear APK de CaféTV" → espera ~3 min (✅ verde).
4. Abre la ejecución y descarga **CafeTV-FireTV** (trae `CafeTV.apk`).

*(Alternativa: abrir la carpeta `android` en Android Studio → Build → Build APK.)*

**Instalar en el Fire TV:**
1. Configuración → Mi Fire TV → Opciones para desarrolladores → activa
   "Aplicaciones de origen desconocido" (o permíteselo a la app *Downloader*).
2. Instala **Downloader** desde la tienda de Amazon.
3. Sube `CafeTV.apk` a algún enlace directo (Google Drive con enlace público,
   Dropbox, etc.), escríbelo en Downloader e instala.
4. CaféTV aparecerá en "Tus apps y canales".

## 2. Samsung TV (Tizen)

Samsung solo permite instalar apps propias en modo desarrollador:
1. Instala **Tizen Studio** en tu PC (con "TV Extensions" y "Samsung Certificate Extension").
2. En el TV: Apps → presiona 1-2-3-4-5 en el control → activa **Developer mode**
   y escribe la IP de tu PC → reinicia el TV.
3. En Tizen Studio: *Device Manager* → conecta la IP del TV.
4. *Certificate Manager* → crea un certificado **Samsung** (pide cuenta Samsung;
   selecciona tu TV para incluir su DUID).
5. *File → Import → Tizen → Tizen Project* → elige la carpeta `tizen`.
6. Clic derecho en el proyecto → **Run As → Tizen Web Application**. Se instala
   y queda en la pantalla de Apps.

Si cambias `web/index.html`, cópialo también a `tizen/index.html`.

## Controles
- Flechas + OK: navegar · Atrás: volver / salir
- Viendo un canal: ▲▼ o CH+/CH− cambian de canal · OK muestra el menú
  (Favorito, Otra fuente, Salir) · Botón rojo en la lista: marcar favorito

## Actualizaciones automáticas
La app instalada (Fire TV y Samsung) abre `start.html`, que descarga la última
versión de `web/index.html` desde https://wilve7192-arch.github.io/cafetv/web/ .
Para cambiar la app basta con modificar `web/index.html` en GitHub: en unos
minutos todos los TV la reciben al abrir CaféTV. Sin internet usa la última
versión guardada. Solo hay que reinstalar si cambia el código Android/Tizen.
