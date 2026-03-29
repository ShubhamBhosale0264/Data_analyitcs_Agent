from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.datasets.models import Dataset
from apps.analysis.models import DataProfile


class DataProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dataset_pk):
        dataset = get_object_or_404(Dataset, pk=dataset_pk)
        profile = get_object_or_404(DataProfile, dataset=dataset)
        return Response({
            "dataset_id": str(dataset.id),
            "ai_narrative": profile.ai_narrative,
            "key_insights": profile.key_insights,
            "completeness_score": profile.completeness_score,
        })


class NLQueryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dataset_pk):
        from apps.analysis.tasks import run_nl_query_task
        from apps.analysis.models import NLQueryResult
        dataset = get_object_or_404(Dataset, pk=dataset_pk)
        question = request.data.get("question", "")
        nl_query = NLQueryResult.objects.create(
            dataset=dataset, asked_by=request.user, question=question
        )
        run_nl_query_task.delay(str(nl_query.id))
        return Response({"query_id": str(nl_query.id)}, status=202)
