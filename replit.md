# MP3 Juice API - Recherche et Téléchargement de Musique

## Description
API Flask qui permet de rechercher et télécharger de la musique (MP3/MP4) en utilisant yt-dlp comme backend.

## Structure du Projet
```
├── main.py           # Application Flask principale
├── requirements.txt  # Dépendances Python
└── replit.md         # Documentation du projet
```

## Routes API

### GET /
Page d'accueil avec documentation des routes.

### GET /recherche?audio=<query>&limit=10
Recherche de musique dynamique.

**Paramètres:**
- `audio` (requis): Terme de recherche
- `limit` (optionnel): Nombre de résultats (1-20, défaut: 10)

**Exemple:** `/recherche?audio=odyai`

**Réponse JSON:**
```json
{
  "recherche": "odyai",
  "nombre_resultats": 10,
  "resultats": [
    {
      "titre": "Nom de la chanson",
      "duree": "3:26",
      "duree_secondes": 206,
      "taille_mp3": "1.20 MB",
      "taille_mp4": "~10-50 MB",
      "url_mp3": "https://...",
      "url_mp4": "https://...",
      "video_id": "abc123",
      "youtube_url": "https://www.youtube.com/watch?v=abc123",
      "telecharger_mp3": "/telecharger/mp3/abc123",
      "telecharger_mp4": "/telecharger/mp4/abc123"
    }
  ]
}
```

### GET /telecharger/mp3/<video_id>
Télécharge le fichier audio MP3 directement.

### GET /telecharger/mp4/<video_id>
Télécharge le fichier vidéo MP4 directement.

### GET /stream/mp3/<video_id>
Obtient l'URL de streaming direct pour l'audio.

## Téléchargement sur téléphone
Pour télécharger sur votre téléphone, utilisez les URLs dans le champ `url_mp3` ou `url_mp4` du JSON, ou accédez aux routes `/telecharger/mp3/<video_id>` et `/telecharger/mp4/<video_id>`.

## Technologies
- Flask 3.0.0
- yt-dlp (extraction YouTube)
- Python 3.11

## Exécution
```bash
python main.py
```
Le serveur démarre sur le port 5000.
