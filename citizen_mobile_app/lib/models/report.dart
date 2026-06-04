class InfractionReport {
  final String violationType;
  final String? plateNumber;
  final double latitude;
  final double longitude;
  final String imagePath;
  final String timestamp;
  final String description;

  InfractionReport({
    required this.violationType,
    this.plateNumber,
    required this.latitude,
    required this.longitude,
    required this.imagePath,
    required this.timestamp,
    required this.description,
  });

  Map<String, dynamic> toJson() {
    return {
      'violation_type': violationType,
      'plate_number': plateNumber,
      'latitude': latitude,
      'longitude': longitude,
      'image_path': imagePath,
      'timestamp': timestamp,
      'description': description,
    };
  }
}
