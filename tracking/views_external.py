"""
External Data Views - Solvey Pharma Integration
External API veya database'den veri çeken view'lar
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .external_service import get_external_api_service, get_external_db_service
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_users(request):
    """
    Solvey database'den kullanıcıları çek
    GET /api/external/users/
    """
    try:
        db_service = get_external_db_service()
        users = db_service.get_users()
        
        return Response({
            'success': True,
            'count': len(users),
            'users': users,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching users: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_orders(request):
    """
    Solvey database'den siparişleri çek
    GET /api/external/orders/?user_id=123
    """
    try:
        user_id = request.query_params.get('user_id')
        if user_id:
            user_id = int(user_id)
        
        db_service = get_external_db_service()
        orders = db_service.get_orders(user_id)
        
        return Response({
            'success': True,
            'count': len(orders),
            'orders': orders,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching orders: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_cities(request):
    """
    Solvey database'den şehir listesini çek
    GET /api/external/cities/?region_id=123
    """
    try:
        region_id = request.query_params.get('region_id')
        if region_id:
            region_id = int(region_id)
        
        db_service = get_external_db_service()
        cities = db_service.get_cities(region_id)
        
        return Response({
            'success': True,
            'count': len(cities),
            'cities': cities,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching cities: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_tables(request):
    """
    Solvey database'deki tüm tabloları listele
    GET /api/external/tables/
    """
    try:
        db_service = get_external_db_service()
        tables = db_service.get_tables()
        
        return Response({
            'success': True,
            'count': len(tables),
            'tables': tables
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching tables: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_table_info(request):
    """
    Bir tablonun kolonlarını listele
    GET /api/external/table-info/?table=orders
    """
    try:
        table_name = request.query_params.get('table')
        if not table_name:
            return Response({
                'success': False,
                'error': 'table parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        db_service = get_external_db_service()
        columns = db_service.get_table_columns(table_name)
        
        return Response({
            'success': True,
            'table': table_name,
            'columns': columns
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching table info: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_doctors(request):
    """
    Solvey database'den doktor listesini çek
    GET /api/external/doctors/
    """
    try:
        db_service = get_external_db_service()
        doctors = db_service.get_doctors()
        
        return Response({
            'success': True,
            'count': len(doctors),
            'doctors': doctors,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching doctors: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_regions_areas(request):
    """
    Solvey database'den bölge alanlarını çek
    GET /api/external/regions-areas/
    """
    try:
        db_service = get_external_db_service()
        areas = db_service.get_regions_areas()
        
        return Response({
            'success': True,
            'count': len(areas),
            'areas': areas,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching regions areas: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_hospitals(request):
    """
    Solvey database'den hastane listesini çek
    GET /api/external/hospitals/
    """
    try:
        db_service = get_external_db_service()
        hospitals = db_service.get_hospitals()
        
        return Response({
            'success': True,
            'count': len(hospitals),
            'hospitals': hospitals,
            'source': 'database'
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching hospitals: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def external_custom_data(request):
    """
    Solvey database'den özel tablo verilerini çek
    GET /api/external/custom/?table=products&category=electronics
    """
    try:
        table_name = request.query_params.get('table')
        if not table_name:
            return Response({
                'success': False,
                'error': 'table parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtreleri al
        filters = {}
        for key, value in request.query_params.items():
            if key != 'table' and key != 'use_api':
                filters[key] = value
        
        # Limit ekle (güvenlik için)
        limit = int(request.query_params.get('limit', 100))
        if limit > 1000:
            limit = 1000
        
        db_service = get_external_db_service()
        data = db_service.get_custom_data(table_name, filters if filters else None)
        
        # Limit uygula
        if len(data) > limit:
            data = data[:limit]
        
        return Response({
            'success': True,
            'count': len(data),
            'table': table_name,
            'data': data
        })
    except Exception as e:
        logger.error(f"[EXTERNAL] Error fetching custom data: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
