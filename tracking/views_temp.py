# Notification Views - to be added to views.py

class NotificationListView(generics.ListAPIView):
    """Kullanıcının bildirimlerini listele"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationCreateView(APIView):
    """Dashboard'dan kullanıcıya bildirim gönder (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        notification_type = request.data.get('notification_type', 'message')
        title = request.data.get('title')
        message = request.data.get('message')
        
        if not user_id or not title or not message:
            return Response(
                {"detail": "user_id, title və message lazımdır."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "İstifadəçi tapılmadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_201_CREATED
        )


class NotificationMarkReadView(APIView):
    """Bildirimi okundu olarak işaretle"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return Response({"message": "Bildirim oxundu olaraq işarələndi."})
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Bildirim tapılmadı."},
                status=status.HTTP_404_NOT_FOUND
            )

