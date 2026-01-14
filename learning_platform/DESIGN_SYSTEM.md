# EduSphere Design System

## 🎨 Palette de Couleurs

### Couleurs Principales
| Variable | Valeur | Utilisation |
|----------|--------|-------------|
| `--primary-darkest` | `#222831` | Arrière-plan principal, éléments les plus sombres |
| `--primary-dark` | `#393E46` | Cartes, navbar, conteneurs |
| `--primary-medium` | `#948979` | Accents, bordures, icônes |
| `--primary-light` | `#DFD0B8` | Texte principal, gradients, hovers |

### Variations Autorisées

#### Arrière-plans
| Variable | Valeur | Utilisation |
|----------|--------|-------------|
| `--bg-main` | `#222831` | Body, arrière-plan général |
| `--bg-card` | `#393E46` | Cartes, conteneurs |
| `--bg-input` | `#2d3139` | Champs de formulaire |
| `--bg-hover` | `#434850` | États hover des éléments |

#### Textes
| Variable | Valeur | Utilisation |
|----------|--------|-------------|
| `--text-primary` | `#DFD0B8` | Texte principal |
| `--text-secondary` | `#c5b8a8` | Texte secondaire |
| `--text-muted` | `#9a8f80` | Texte désactivé, placeholders |
| `--text-heading` | `#e8dccf` | Titres importants |

#### Accents
| Variable | Valeur | Utilisation |
|----------|--------|-------------|
| `--accent-primary` | `#948979` | Boutons, liens, accents |
| `--accent-hover` | `#a59a88` | États hover des accents |
| `--accent-active` | `#837967` | États actifs |
| `--accent-subtle` | `#6d6556` | Accents très subtils |

#### États (Désaturés)
| Variable | Valeur | Utilisation |
|----------|--------|-------------|
| `--success` | `#8b9479` | Succès, validations |
| `--success-text` | `#a5b08f` | Texte de succès |
| `--warning` | `#94896f` | Avertissements |
| `--warning-text` | `#aa9f85` | Texte d'avertissement |
| `--error` | `#8b7979` | Erreurs, suppression |
| `--error-text` | `#a18f8f` | Texte d'erreur |
| `--info` | `#79888b` | Informations |
| `--info-text` | `#8f9ea1` | Texte informatif |

---

## 🧱 Composants

### Boutons

```html
<!-- Bouton Principal -->
<button class="btn-primary">
    <i class="fas fa-check"></i>
    Action principale
</button>

<!-- Bouton Secondaire -->
<button class="btn-secondary">
    <i class="fas fa-times"></i>
    Annuler
</button>

<!-- Bouton Danger -->
<button class="btn-danger">
    <i class="fas fa-trash"></i>
    Supprimer
</button>

<!-- Bouton Icône -->
<button class="btn-icon">
    <i class="fas fa-edit"></i>
</button>
```

### Cartes

```html
<!-- Carte avec hover -->
<div class="card">
    Contenu avec effet hover (élévation + bordure)
</div>

<!-- Carte statique -->
<div class="card-static">
    Contenu sans animation hover
</div>
```

### Formulaires

```html
<div>
    <label class="form-label">Champ label</label>
    <input type="text" class="form-input" placeholder="Placeholder...">
</div>
```

### Barres de Progression

```html
<div class="progress-bar">
    <div class="progress-fill" style="width: 75%"></div>
</div>
```

### Navigation

```html
<a href="#" class="nav-link">
    <i class="fas fa-home"></i>
    <span>Accueil</span>
</a>

<a href="#" class="nav-link active">
    <i class="fas fa-book"></i>
    <span>Cours</span>
</a>
```

---

## 📐 Typographie

### Hiérarchie des Titres

| Élément | Taille | Poids | Couleur |
|---------|--------|-------|---------|
| H1 | 2.5rem (40px) | 700 | `--text-heading` |
| H2 | 1.875rem (30px) | 600 | `--text-primary` |
| H3 | 1.5rem (24px) | 600 | `--text-primary` |
| Corps | 1rem (16px) | 400 | `--text-primary` |
| Secondaire | 0.875rem (14px) | 400 | `--text-secondary` |
| Muted | 0.875rem (14px) | 400 | `--text-muted` |

### Police
- **Famille principale**: Inter (Google Fonts)
- **Fallback**: -apple-system, BlinkMacSystemFont, sans-serif

---

## 🌟 Effets Visuels

### Ombres

```css
--shadow-xs: 0 1px 2px rgba(34, 40, 49, 0.05);
--shadow-sm: 0 2px 4px rgba(34, 40, 49, 0.1);
--shadow-md: 0 4px 8px rgba(34, 40, 49, 0.15), 0 2px 4px rgba(34, 40, 49, 0.1);
--shadow-lg: 0 8px 16px rgba(34, 40, 49, 0.2), 0 4px 8px rgba(34, 40, 49, 0.15);
--shadow-xl: 0 12px 24px rgba(34, 40, 49, 0.25), 0 6px 12px rgba(34, 40, 49, 0.2);
```

### Glassmorphism (Navbar)

```css
.glass {
    background: rgba(57, 62, 70, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(148, 137, 121, 0.15);
}
```

### Gradients

```css
/* Gradient pour icônes/boutons */
background: linear-gradient(135deg, var(--primary-medium), var(--primary-light));

/* Gradient pour texte */
background: linear-gradient(135deg, #DFD0B8, #948979);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### Glow Effect (Cartes)

```html
<div class="group relative">
    <div class="absolute -inset-0.5 bg-gradient-to-r from-[#948979] to-[#DFD0B8] 
                rounded-2xl opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-500">
    </div>
    <div class="relative card-static p-6">
        Contenu de la carte
    </div>
</div>
```

---

## 🎯 Patterns d'Utilisation

### États de l'Interface

| État | Couleur Background | Couleur Bordure | Couleur Texte |
|------|-------------------|-----------------|---------------|
| Succès | `#8b9479/20` | `#8b9479/30` | `#a5b08f` |
| Avertissement | `#94896f/20` | `#94896f/30` | `#aa9f85` |
| Erreur | `#8b7979/20` | `#8b7979/30` | `#a18f8f` |
| Info | `#79888b/20` | `#79888b/30` | `#8f9ea1` |

### Animations

- **Durée standard**: 300ms
- **Durée longue**: 500ms
- **Easing**: `cubic-bezier(0.4, 0, 0.2, 1)`
- **Transitions**: `all 300ms cubic-bezier(0.4, 0, 0.2, 1)`

---

## ⚠️ Règles Strictes

### INTERDIT

❌ Classes Tailwind de couleurs standards (`bg-blue-600`, `text-red-400`, `gray-800`)  
❌ Couleurs HEX/RGB hors de la palette définie  
❌ Gradients avec couleurs non-palette  
❌ Ombres avec couleurs non-palette  

### AUTORISÉ

✅ Uniquement les 4 couleurs principales et leurs variations  
✅ Les couleurs d'état (désaturées)  
✅ Le blanc pour les textes sur fond coloré  
✅ Les transparences (rgba) des couleurs de la palette  

---

## 📁 Structure des Fichiers

```
templates/
├── base.html                 # Template de base avec navbar/footer
├── home.html                 # Page d'accueil
├── courses/
│   ├── course_list.html
│   ├── course_detail.html
│   ├── course_form.html
│   └── course_confirm_delete.html
├── modules/
│   ├── module_list.html
│   ├── module_form.html
│   └── module_confirm_delete.html
├── evaluations/
│   ├── evaluation_form.html
│   ├── take_quiz.html
│   ├── quiz_results.html
│   ├── submit_assignment.html
│   ├── submission_list.html
│   └── grade_submission.html
├── questions/
│   ├── question_list.html
│   ├── question_form.html
│   └── question_confirm_delete.html
├── resources/
│   ├── resource_form.html
│   └── resource_confirm_delete.html
├── students/
│   └── dashboard.html
├── teachers/
│   └── dashboard.html
├── certificates/
│   └── certificate_list.html
├── notifications/
│   └── notification_list.html
└── registration/
    ├── login.html
    └── signup.html
```

---

## 🔧 Configuration Requise

### Dépendances CDN (dans base.html)

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Font Awesome -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<!-- Google Fonts - Inter -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```
