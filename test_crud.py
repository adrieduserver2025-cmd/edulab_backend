import asyncio
import httpx

BASE = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "mock-admin-token"
headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

async def test_admin_crud():
    results = []
    async with httpx.AsyncClient() as client:

        # 1. Auth
        print("--- Verify Admin Auth ---")
        me = await client.get(f"{BASE}/auth/me", headers=headers)
        print(f"GET /auth/me: {me.status_code}")
        if me.status_code == 200:
            user = me.json()
            print(f"  Role: {user.get('role')}, Email: {user.get('email')}")
            results.append(("Admin Auth", True))
        else:
            print(f"  Error: {me.text[:200]}")
            results.append(("Admin Auth", False))
            return

        # 2. List Organizations
        print("\n--- List Organizations ---")
        orgs = await client.get(f"{BASE}/admin/organizations", headers=headers)
        print(f"GET /admin/organizations: {orgs.status_code}")
        orgs_data = orgs.json() if orgs.status_code == 200 else []
        print(f"  Count: {len(orgs_data)}")
        results.append(("List Organizations", orgs.status_code == 200))

        # 3. List Programs
        print("\n--- List Programs ---")
        progs = await client.get(f"{BASE}/admin/programs", headers=headers)
        print(f"GET /admin/programs: {progs.status_code}")
        progs_data = progs.json() if progs.status_code == 200 else []
        print(f"  Count: {len(progs_data)}")
        results.append(("List Programs", progs.status_code == 200))

        # 4. List Applications
        print("\n--- List Applications (admin) ---")
        apps = await client.get(f"{BASE}/applications/admin", headers=headers)
        print(f"GET /applications/admin: {apps.status_code}")
        apps_data = apps.json() if apps.status_code == 200 else []
        print(f"  Count: {len(apps_data)}")
        results.append(("List Applications", apps.status_code == 200))

        # 5. Edit Organization
        if orgs_data:
            org_id = orgs_data[0]["id"]
            original_name = orgs_data[0]["name"]
            org_status = orgs_data[0].get("status", "PENDING")
            print(f"\n--- Edit Organization {org_id} ---")
            edit = await client.put(
                f"{BASE}/admin/organizations/{org_id}",
                json={"name": original_name + " EDITED", "status": org_status},
                headers=headers
            )
            print(f"PUT /admin/organizations/{org_id}: {edit.status_code}")
            ok = edit.status_code == 200
            if ok:
                print(f"  Updated name: {edit.json().get('name')}")
                restore = await client.put(
                    f"{BASE}/admin/organizations/{org_id}",
                    json={"name": original_name},
                    headers=headers
                )
                print(f"  Restore: {restore.status_code}")
            else:
                print(f"  Error: {edit.text[:200]}")
            results.append(("Edit Organization", ok))

        # 6. Edit Program
        if progs_data:
            prog_id = progs_data[0]["id"]
            original_desc = progs_data[0].get("description", "")
            original_title = progs_data[0].get("title", "")
            print(f"\n--- Edit Program {prog_id} ---")
            edit = await client.put(
                f"{BASE}/admin/programs/{prog_id}",
                json={"title": original_title, "description": original_desc + " (EDITED)"},
                headers=headers
            )
            print(f"PUT /admin/programs/{prog_id}: {edit.status_code}")
            ok = edit.status_code == 200
            if ok:
                print("  Edit OK")
                restore = await client.put(
                    f"{BASE}/admin/programs/{prog_id}",
                    json={"title": original_title, "description": original_desc},
                    headers=headers
                )
                print(f"  Restore: {restore.status_code}")
            else:
                print(f"  Error: {edit.text[:300]}")
            results.append(("Edit Program", ok))

        # 7. Test hero endpoint exists (opportunity detail page)
        print("\n--- Opportunity Slugs (Hero page) ---")
        opp = await client.get(f"{BASE}/opportunities/aiesec-voluntariado")
        print(f"GET /opportunities/aiesec-voluntariado: {opp.status_code}")
        results.append(("Opportunity Detail Page", opp.status_code == 200))

        print("\n=============================")
        print("     FINAL TEST RESULTS      ")
        print("=============================")
        all_pass = True
        for name, passed in results:
            status_str = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  [{status_str}] {name}")
        print("=============================")
        print(f"  OVERALL: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
        print("=============================")

asyncio.run(test_admin_crud())
