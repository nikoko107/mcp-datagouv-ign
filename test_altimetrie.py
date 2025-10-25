#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités d'altimétrie IGN
"""

import asyncio
import httpx
from ign_geo_services import IGNGeoServices


async def test_resources():
    """Test de récupération des ressources altimétriques"""
    print("\n=== Test: Récupération des ressources altimétriques ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            result = await ign.get_altimetry_resources(client)

            if isinstance(result, list):
                print(f"✓ Nombre de ressources: {len(result)}")
                if result:
                    print(f"✓ Première ressource: {result[0].get('id', 'N/A')}")
            elif isinstance(result, dict) and 'resources' in result:
                resources = result['resources']
                print(f"✓ Nombre de ressources: {len(resources)}")
                if resources:
                    print(f"✓ Première ressource: {resources[0].get('id', 'N/A')}")
            else:
                print(f"✓ Ressources récupérées")

            print("✓ Récupération des ressources réussie !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_elevation_single_point():
    """Test de récupération d'altitude pour un point unique"""
    print("\n=== Test: Altitude du Mont Blanc ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Mont Blanc (6.8651, 45.8326)
            result = await ign.get_elevation(
                client=client,
                lon="6.8651",
                lat="45.8326",
                resource="ign_rge_alti_wld",
                delimiter="|",
                zonly=False
            )

            if 'elevations' in result and len(result['elevations']) > 0:
                elev = result['elevations'][0]
                print(f"✓ Longitude: {elev.get('lon')}")
                print(f"✓ Latitude: {elev.get('lat')}")
                print(f"✓ Altitude: {elev.get('z')} mètres")
                print(f"✓ Précision: {elev.get('acc', 'N/A')}")
            else:
                print(f"✓ Résultat: {result}")

            print("✓ Récupération d'altitude réussie !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_elevation_multiple_points():
    """Test de récupération d'altitude pour plusieurs points"""
    print("\n=== Test: Altitudes de 3 points en France ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Paris, Lyon, Marseille
            result = await ign.get_elevation(
                client=client,
                lon="2.3522|4.8357|5.3698",
                lat="48.8566|45.7640|43.2965",
                resource="ign_rge_alti_wld"
            )

            if 'elevations' in result:
                print(f"✓ Nombre de points: {len(result['elevations'])}")
                for i, elev in enumerate(result['elevations'], 1):
                    print(f"  Point {i}: alt={elev.get('z')}m à ({elev.get('lon')}, {elev.get('lat')})")
            else:
                print(f"✓ Résultat: {result}")

            print("✓ Récupération multiple réussie !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_elevation_line():
    """Test de calcul de profil altimétrique"""
    print("\n=== Test: Profil altimétrique Paris → Versailles ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Paris (2.3522, 48.8566) -> Versailles (2.1242, 48.8049)
            result = await ign.get_elevation_line(
                client=client,
                lon="2.3522|2.1242",
                lat="48.8566|48.8049",
                resource="ign_rge_alti_wld",
                profile_mode="simple",
                sampling=30
            )

            if 'elevations' in result:
                print(f"✓ Nombre de points du profil: {len(result['elevations'])}")

            if 'height_differences' in result:
                hd = result['height_differences']
                print(f"✓ Dénivelé positif: {hd.get('positive', 0)} m")
                print(f"✓ Dénivelé négatif: {hd.get('negative', 0)} m")

            print("✓ Calcul de profil altimétrique réussi !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_elevation_line_mountain():
    """Test de profil altimétrique en montagne"""
    print("\n=== Test: Profil altimétrique en montagne (Grenoble → Alpe d'Huez) ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Grenoble (5.7243, 45.1885) -> Alpe d'Huez (6.0709, 45.0904)
            result = await ign.get_elevation_line(
                client=client,
                lon="5.7243|6.0709",
                lat="45.1885|45.0904",
                resource="ign_rge_alti_wld",
                profile_mode="accurate",
                sampling=100
            )

            if 'elevations' in result:
                elevations = result['elevations']
                print(f"✓ Nombre de points: {len(elevations)}")
                if elevations:
                    min_alt = min(e.get('z', 0) for e in elevations if e.get('z') is not None)
                    max_alt = max(e.get('z', 0) for e in elevations if e.get('z') is not None)
                    print(f"✓ Altitude min: {min_alt:.1f} m")
                    print(f"✓ Altitude max: {max_alt:.1f} m")

            if 'height_differences' in result:
                hd = result['height_differences']
                print(f"✓ Dénivelé positif: {hd.get('positive', 0):.1f} m")
                print(f"✓ Dénivelé négatif: {hd.get('negative', 0):.1f} m")

            print("✓ Profil montagnard réussi !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def main():
    """Exécute tous les tests"""
    print("Démarrage des tests d'altimétrie IGN...")

    await test_resources()
    await test_elevation_single_point()
    await test_elevation_multiple_points()
    await test_elevation_line()
    await test_elevation_line_mountain()

    print("\n=== Tous les tests terminés ===\n")


if __name__ == "__main__":
    asyncio.run(main())
