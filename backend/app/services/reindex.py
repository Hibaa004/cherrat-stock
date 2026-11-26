def reindex(med_id: int) -> None:
    try:
        from .rag_service import index_medicament

        index_medicament(med_id)
    except Exception as e:
        print('Indexation IA ignorée :', e)
