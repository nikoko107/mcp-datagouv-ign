#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités de navigation IGN
"""

import asyncio
import httpx
from ign_geo_services import IGNGeoServices


async def test_route():
    """Test du calcul d'itinéraire"""
    print("\n=== Test: Calcul d'itinéraire Paris -> Lyon ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Paris (2.3522, 48.8566) -> Lyon (4.8357, 45.7640)
            result = await ign.calculate_route(
                client=client,
                start="2.3522,48.8566",
                end="4.8357,45.7640",
                resource="bdtopo-osrm",
                profile="car",
                optimization="fastest",
                get_steps=True
            )

            print(f"✓ Distance: {result.get('distance')} km")
            print(f"✓ Durée: {result.get('duration')} heures")
            print(f"✓ BBox: {result.get('bbox')}")
            print(f"✓ Nombre d'étapes: {len(result.get('portions', []))}")
            print("✓ Calcul d'itinéraire réussi !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_isochrone():
    """Test du calcul d'isochrone"""
    print("\n=== Test: Isochrone 30 minutes depuis Paris ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Centre de Paris (2.3522, 48.8566)
            result = await ign.calculate_isochrone(
                client=client,
                point="2.3522,48.8566",
                cost_value=0.5,  # 30 minutes = 0.5 heures
                cost_type="time",
                resource="bdtopo-valhalla",
                profile="car",
                direction="departure",
                time_unit="hour"
            )

            print(f"✓ Type de géométrie: {result.get('geometry', {}).get('type')}")
            print(f"✓ Coût: {result.get('costValue')} {result.get('costType')}")
            print("✓ Calcul d'isochrone réussi !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def test_capabilities():
    """Test de récupération des capacités"""
    print("\n=== Test: Récupération des capacités ===")

    ign = IGNGeoServices()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            result = await ign.get_route_capabilities(client)

            print(f"✓ Nombre de ressources: {len(result.get('resources', []))}")
            if 'resources' in result:
                print(f"✓ Ressources disponibles:")
                for resource in result['resources'][:3]:
                    print(f"  - {resource.get('id')}")
            print("✓ Récupération des capacités réussie !")

        except Exception as e:
            print(f"✗ Erreur: {e}")


async def main():
    """Exécute tous les tests"""
    print("Démarrage des tests de navigation IGN...")

    await test_capabilities()
    await test_route()
    await test_isochrone()

    print("\n=== Tous les tests terminés ===\n")


if __name__ == "__main__":
    asyncio.run(main())
