"""
Location-based models for Employee Check-in System
"""
import logging
import math
from typing import List, Optional, Dict, Any, Tuple
from database import DatabaseManager, DatabaseConnectionError, DatabaseQueryError
from security_utils import sanitize_user_input

logger = logging.getLogger(__name__)


class LocationSetting:
    """Model for location settings"""
    
    def __init__(self, id: int, name: str, description: str = None, 
                 latitude: float = None, longitude: float = None, 
                 radius_meters: int = 100, is_active: bool = True, 
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.radius_meters = radius_meters
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LocationSetting to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'radius_meters': self.radius_meters,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class LocationRepository:
    """Repository for location settings operations"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def get_active_locations(self) -> List[LocationSetting]:
        """Get all active location settings"""
        try:
            query = """
                SELECT id, name, description, latitude, longitude, 
                       radius_meters, is_active, created_at, updated_at
                FROM location_settings 
                WHERE is_active = TRUE
                ORDER BY name
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            locations = []
            
            for row in results:
                location = LocationSetting(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    radius_meters=row['radius_meters'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                locations.append(location)
            
            return locations
            
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error getting active locations: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error getting active locations: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting active locations: {e}")
            raise DatabaseQueryError(f"Failed to get active locations: {e}")
    
    def get_all_locations(self) -> List[LocationSetting]:
        """Get all location settings (active and inactive)"""
        try:
            query = """
                SELECT id, name, description, latitude, longitude, 
                       radius_meters, is_active, created_at, updated_at
                FROM location_settings 
                ORDER BY is_active DESC, name
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            locations = []
            
            for row in results:
                location = LocationSetting(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    radius_meters=row['radius_meters'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                locations.append(location)
            
            return locations
            
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error getting all locations: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error getting all locations: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting all locations: {e}")
            raise DatabaseQueryError(f"Failed to get all locations: {e}")
    
    def get_location_by_id(self, location_id: int) -> Optional[LocationSetting]:
        """Get location setting by ID"""
        try:
            query = """
                SELECT id, name, description, latitude, longitude, 
                       radius_meters, is_active, created_at, updated_at
                FROM location_settings 
                WHERE id = %s
            """
            
            results = self.db_manager.execute_query(query, (location_id,), fetch_results=True)
            result = results[0] if results else None
            
            if result:
                return LocationSetting(
                    id=result['id'],
                    name=result['name'],
                    description=result['description'],
                    latitude=result['latitude'],
                    longitude=result['longitude'],
                    radius_meters=result['radius_meters'],
                    is_active=result['is_active'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at']
                )
            
            return None
            
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error getting location {location_id}: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error getting location {location_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting location {location_id}: {e}")
            raise DatabaseQueryError(f"Failed to get location {location_id}: {e}")
    
    def create_location(self, name: str, description: str, latitude: float, 
                       longitude: float, radius_meters: int = 100) -> LocationSetting:
        """Create new location setting"""
        try:
            # Sanitize inputs
            name = sanitize_user_input(name)
            description = sanitize_user_input(description) if description else None
            
            # Validate coordinates
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            if radius_meters < 1 or radius_meters > 10000:
                raise ValueError("Radius must be between 1 and 10000 meters")
            
            query = """
                INSERT INTO location_settings (name, description, latitude, longitude, radius_meters)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query(query, (name, description, latitude, longitude, radius_meters))
            
            # Get the created location by finding the most recent one with matching data
            find_query = """
                SELECT id FROM location_settings 
                WHERE name = %s AND latitude = %s AND longitude = %s 
                ORDER BY created_at DESC LIMIT 1
            """
            results = self.db_manager.execute_query(find_query, (name, latitude, longitude), fetch_results=True)
            
            if results:
                location_id = results[0]['id']
                return self.get_location_by_id(location_id)
            else:
                raise DatabaseQueryError("Failed to retrieve created location")
            
        except ValueError as e:
            logger.error(f"Validation error creating location: {e}")
            raise
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error creating location: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error creating location: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating location: {e}")
            raise DatabaseQueryError(f"Failed to create location: {e}")
    
    def update_location(self, location_id: int, name: str = None, description: str = None,
                       latitude: float = None, longitude: float = None, 
                       radius_meters: int = None, is_active: bool = None) -> LocationSetting:
        """Update location setting"""
        try:
            # Get existing location
            existing_location = self.get_location_by_id(location_id)
            if not existing_location:
                raise ValueError(f"Location with ID {location_id} not found")
            
            # Prepare update data
            updates = []
            params = []
            
            if name is not None:
                name = sanitize_user_input(name)
                updates.append("name = %s")
                params.append(name)
            
            if description is not None:
                description = sanitize_user_input(description) if description else None
                updates.append("description = %s")
                params.append(description)
            
            if latitude is not None:
                if not (-90 <= latitude <= 90):
                    raise ValueError("Latitude must be between -90 and 90")
                updates.append("latitude = %s")
                params.append(latitude)
            
            if longitude is not None:
                if not (-180 <= longitude <= 180):
                    raise ValueError("Longitude must be between -180 and 180")
                updates.append("longitude = %s")
                params.append(longitude)
            
            if radius_meters is not None:
                if radius_meters < 1 or radius_meters > 10000:
                    raise ValueError("Radius must be between 1 and 10000 meters")
                updates.append("radius_meters = %s")
                params.append(radius_meters)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            
            if not updates:
                return existing_location
            
            # Add updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(location_id)
            
            query = f"""
                UPDATE location_settings 
                SET {', '.join(updates)}
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, params)
            
            # Return updated location
            return self.get_location_by_id(location_id)
            
        except ValueError as e:
            logger.error(f"Validation error updating location {location_id}: {e}")
            raise
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error updating location {location_id}: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error updating location {location_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating location {location_id}: {e}")
            raise DatabaseQueryError(f"Failed to update location {location_id}: {e}")
    
    def delete_location(self, location_id: int) -> bool:
        """Delete location setting (soft delete by setting is_active = FALSE)"""
        try:
            query = """
                UPDATE location_settings 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, (location_id,))
            return True
            
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error deleting location {location_id}: {e}")
            raise
        except DatabaseQueryError as e:
            logger.error(f"Database query error deleting location {location_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting location {location_id}: {e}")
            raise DatabaseQueryError(f"Failed to delete location {location_id}: {e}")


class LocationValidator:
    """Utility class for location validation"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in meters
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        
        return c * r
    
    @staticmethod
    def is_within_radius(user_lat: float, user_lon: float, 
                        location_lat: float, location_lon: float, 
                        radius_meters: int) -> Tuple[bool, float]:
        """
        Check if user location is within allowed radius
        Returns (is_within, distance_meters)
        """
        distance = LocationValidator.calculate_distance(
            user_lat, user_lon, location_lat, location_lon
        )
        
        is_within = distance <= radius_meters
        return is_within, distance
    
    @staticmethod
    def validate_user_location(user_lat: float, user_lon: float, 
                             allowed_locations: List[LocationSetting]) -> Tuple[bool, Optional[LocationSetting], float]:
        """
        Validate if user is within any allowed location
        Returns (is_valid, matched_location, distance)
        """
        if not allowed_locations:
            return False, None, 0
        
        for location in allowed_locations:
            is_within, distance = LocationValidator.is_within_radius(
                user_lat, user_lon, 
                location.latitude, location.longitude, 
                location.radius_meters
            )
            
            if is_within:
                return True, location, distance
        
        # Find closest location for error message
        closest_location = None
        min_distance = float('inf')
        
        for location in allowed_locations:
            _, distance = LocationValidator.is_within_radius(
                user_lat, user_lon,
                location.latitude, location.longitude,
                location.radius_meters
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_location = location
        
        return False, closest_location, min_distance