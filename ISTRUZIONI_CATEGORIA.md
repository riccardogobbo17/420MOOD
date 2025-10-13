# Istruzioni per aggiungere il sistema di categorie

## ✅ Modifiche completate nel codice

Ho implementato il sistema di categorie nell'applicazione. Tutte le pagine ora rispettano la categoria selezionata nella Homepage.

### File modificati:
1. **`Home.py`** - Aggiunto selettore categoria e filtro per categoria
2. **`pages/1_Partite.py`** - Filtro per categoria attiva
3. **`pages/2_Stats.py`** - Filtro per categoria attiva
4. **`pages/6_Video.py`** - Filtro per categoria attiva
5. **`pages/7_Admin.py`** - Campo categoria nel form di inserimento partita

## 🗄️ Modifiche necessarie al Database

**IMPORTANTE**: Devi aggiungere un campo `categoria` nella tabella `partite` del database Supabase.

### Opzione 1: Tramite interfaccia Supabase (consigliato)

1. Vai su [https://supabase.com](https://supabase.com)
2. Apri il tuo progetto
3. Nel menu laterale, clicca su **Table Editor**
4. Seleziona la tabella **`partite`**
5. Clicca su **"+ New Column"**
6. Compila i campi:
   - **Name**: `categoria`
   - **Type**: `text`
   - **Default Value**: `Prima Squadra`
   - **Allow nullable**: ✅ (opzionale, ma consigliato)
7. Clicca su **Save**

### Opzione 2: Tramite SQL Editor

1. Vai su [https://supabase.com](https://supabase.com)
2. Apri il tuo progetto
3. Nel menu laterale, clicca su **SQL Editor**
4. Esegui questa query:

```sql
-- Aggiungi il campo categoria alla tabella partite
ALTER TABLE partite 
ADD COLUMN categoria TEXT DEFAULT 'Prima Squadra';

-- Aggiorna le partite esistenti con la categoria di default
UPDATE partite 
SET categoria = 'Prima Squadra' 
WHERE categoria IS NULL;
```

## 📋 Come aggiornare le partite esistenti

### Opzione 1: Manualmente tramite interfaccia
1. Vai su **Table Editor** > **partite**
2. Per ogni partita, clicca sulla cella della colonna `categoria`
3. Inserisci la categoria corretta (es: "Prima Squadra", "U19", ecc.)

### Opzione 2: Tramite SQL (se hai molte partite)
```sql
-- Esempio: imposta tutte le partite esistenti come "Prima Squadra"
UPDATE partite 
SET categoria = 'Prima Squadra';

-- Oppure imposta partite specifiche come U19 (esempio)
-- Modifica la WHERE clause in base alle tue esigenze
UPDATE partite 
SET categoria = 'U19' 
WHERE avversario IN ('Avversario1', 'Avversario2');
```

## 🎯 Come funziona

1. **Homepage**: L'utente seleziona la categoria dal menu a tendina
2. **Session State**: La categoria viene memorizzata in `st.session_state['categoria_selezionata']`
3. **Tutte le pagine**: Leggono automaticamente la categoria da session_state e filtrano i dati
4. **Admin**: Quando crei una nuova partita, puoi specificare la categoria

## 📝 Esempi di utilizzo

### Aggiungere una nuova categoria (es: "U19")

1. Vai alla pagina **Admin** (password: `admin`)
2. Inserisci una nuova partita:
   - Data: 2025-01-15
   - Avversario: Squadra XYZ
   - Competizione: Campionato
   - **Categoria**: U19
   - Link YouTube: (opzionale)
3. Salva la partita
4. Carica gli eventi CSV come di consueto

### Visualizzare i dati della U19

1. Vai alla **Homepage**
2. Nel menu a tendina "📂 Seleziona Categoria", scegli **U19**
3. Tutte le pagine ora mostreranno solo i dati della categoria U19

## 🔄 Passare tra categorie

Per passare da una categoria all'altra:
1. Torna alla **Homepage**
2. Cambia la selezione nel menu "📂 Seleziona Categoria"
3. Naviga nelle altre pagine - vedrai i dati filtrati per la nuova categoria

## ⚠️ Note importanti

- Il campo `categoria` nel database è **obbligatorio** per il corretto funzionamento
- Se una partita non ha categoria, verrà usato il default "Prima Squadra"
- Le categorie sono case-sensitive (es: "U19" ≠ "u19")
- Per aggiungere nuove categorie, basta inserirle quando crei nuove partite nell'Admin

## 🎨 Personalizzazione

Se vuoi aggiungere più categorie predefinite, puoi modificare il campo `categoria` nel form di inserimento della pagina Admin (riga 118 di `7_Admin.py`):

```python
# Da:
categoria = st.text_input("Categoria", value="Prima Squadra")

# A (esempio con selectbox):
categoria = st.selectbox("Categoria", ["Prima Squadra", "U19", "U17", "Juniores"])
```

