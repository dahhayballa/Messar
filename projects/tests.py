from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from core.models import ServiceType, Requirement
from projects.models import Project, Investor, NameReservation
from workflow.models import Application, Document
from operations.models import Inspection, Payment, License


class MasarIntegrationTestCase(APITestCase):
    def setUp(self):
        # Création des données de base de test
        self.service_type = ServiceType.objects.create(
            name="وكالة سفر",
            required_inspections_count=2,
            provisional_validity_days=180
        )
        self.req_id = Requirement.objects.create(
            service_type=self.service_type,
            name="بطاقة تعريف",
            required=True
        )
        self.req_other = Requirement.objects.create(
            service_type=self.service_type,
            name="رخصة بلدية",
            required=False
        )

        # Création des comptes utilisateurs de test
        self.inspector_user = User.objects.create_user(
            username="inspector@masar.gov",
            email="inspector@masar.gov",
            phone="+22244444444",
            password="testpassword123",
            role="INSPECTOR"
        )
        self.admin_user = User.objects.create_user(
            username="admin@masar.gov",
            email="admin@masar.gov",
            phone="+22255555555",
            password="testpassword123",
            role="ADMIN"
        )

    def test_complete_investor_journey(self):
        """
        Teste le parcours complet d'Ahmed de A à Z (Chapitres 1 à 11 + Chapitre Final).
        """
        # ==========================================
        # CHAPITRE 1 & 2 : Consultation sans authentification
        # ==========================================
        url_services = reverse("service-list")
        response = self.client.get(url_services)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "وكالة سفر")

        # ==========================================
        # CHAPITRE 3 : Vérification de la disponibilité du nom
        # ==========================================
        url_check_name = reverse("project-check-name")
        response = self.client.get(url_check_name, {"name": "رحلات الصحراء", "service_type": self.service_type.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["available"])

        # ==========================================
        # CHAPITRE 4 : Onboarding atomique
        # ==========================================
        url_onboarding = reverse("project-onboarding")
        onboarding_data = {
            "email": "ahmed@example.com",
            "phone": "+22233333333",
            "password": "ahmedpassword123",
            "investor_type": "PERSON",
            "full_name": "أحمد ولد محمد",
            "nationality": "موريتاني",
            "national_id": "1234567890",
            "project_name": "رحلات الصحراء",
            "service_type": self.service_type.id
        }
        response = self.client.post(url_onboarding, onboarding_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data["id"]

        # Vérifier que les objets ont bien été créés en base de données
        self.assertTrue(User.objects.filter(email="ahmed@example.com").exists())
        self.assertTrue(Investor.objects.filter(full_name="أحمد ولد محمد").exists())
        self.assertTrue(Project.objects.filter(name="رحلات الصحراء").exists())
        self.assertTrue(NameReservation.objects.filter(name="رحلات الصحراء", status="RESERVED").exists())

        # Authentifier le client avec le compte d'Ahmed
        self.client.login(username="ahmed@example.com", password="ahmedpassword123")
        # On peut aussi utiliser la méthode force_authenticate pour DRF
        ahmed_user = User.objects.get(email="ahmed@example.com")
        self.client.force_authenticate(user=ahmed_user)

        # ==========================================
        # CHAPITRE 5 : Localisation du Projet
        # ==========================================
        url_project_detail = reverse("project-detail", kwargs={"pk": project_id})
        location_data = {
            "wilaya": "نواكشوط",
            "moughataa": "تفرغ زينه",
            "address": "شارع المختار ولد داداه",
            "latitude": 18.0858,
            "longitude": -15.9785,
            "service_type": self.service_type.id,
            "name": "رحلات الصحراء"
        }
        response = self.client.put(url_project_detail, location_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["wilaya"], "نواكشوط")
        self.assertEqual(response.data["latitude"], 18.0858)

        # ==========================================
        # CHAPITRE 6 : Smart File et calcul de progression (0%)
        # ==========================================
        url_app_status = reverse("application-detail", kwargs={"project_id": project_id})
        # Créons l'application en base pour tester sa progression
        app_obj, _ = Application.objects.get_or_create(project_id=project_id)
        response = self.client.get(url_app_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["progress_percentage"], 0.0)

        # Upload de la pièce obligatoire (بطاقة تعريف)
        fake_file = SimpleUploadedFile("id_card.jpg", b"fake image content", content_type="image/jpeg")
        url_upload = reverse("document-list")
        upload_data = {
            "project": project_id,
            "requirement": self.req_id.id,
            "file": fake_file
        }
        response = self.client.post(url_upload, upload_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que le pourcentage est passé à 100% (le seul document obligatoire est uploade)
        response = self.client.get(url_app_status)
        self.assertEqual(response.data["progress_percentage"], 100.0)

        # ==========================================
        # CHAPITRE 7 : Soumission de la demande et blocage du nom
        # ==========================================
        url_submit = reverse("application-submit", kwargs={"project_id": project_id})
        response = self.client.post(url_submit)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUBMITTED")

        # Vérifier que la réservation du nom est passée à CONFIRMED (bloqué pendant l'instruction)
        reservation = NameReservation.objects.get(project_id=project_id)
        self.assertEqual(reservation.status, "CONFIRMED")

        # ==========================================
        # CHAPITRE 8 : Inspection terrain avec GPS et checklist
        # ==========================================
        # Passage manuel de l'application à INSPECTION_SCHEDULED par l'administration (simulé)
        app_obj.refresh_from_db()
        app_obj.status = "INSPECTION_SCHEDULED"
        app_obj.save()

        # Planifier l'inspection
        inspection = Inspection.objects.create(
            project_id=project_id,
            inspector=self.inspector_user,
            status="PENDING"
        )

        # Authentifier l'inspecteur
        self.client.force_authenticate(user=self.inspector_user)
        url_report = reverse("inspection-report", kwargs={"pk": inspection.id})
        report_data = {
            "result": "PASSED",
            "notes": "المقر مطابق للشروط والمسافة ممتازة",
            "latitude": 18.0859,
            "longitude": -15.9786,
            "checklist_completed": True
        }
        response = self.client.post(url_report, report_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "PAYMENT_PENDING")

        # ==========================================
        # CHAPITRE 9 : Paiement
        # ==========================================
        # Authentifier Ahmed à nouveau
        self.client.force_authenticate(user=ahmed_user)
        fake_receipt = SimpleUploadedFile("receipt.pdf", b"fake receipt content", content_type="application/pdf")
        url_payment = reverse("payment-list")
        payment_data = {
            "project": project_id,
            "amount": 8000.00,
            "receipt": fake_receipt
        }
        response = self.client.post(url_payment, payment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment_id = response.data["id"]

        # Authentifier l'administrateur
        self.client.force_authenticate(user=self.admin_user)
        url_verify_payment = reverse("payment-verify", kwargs={"pk": payment_id})
        response = self.client.post(url_verify_payment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'application passe en PROVISIONAL_LICENSE
        self.assertEqual(response.data["status"], "PROVISIONAL_LICENSE")

        # ==========================================
        # CHAPITRE 10 : Vérification du permis initial (6 mois)
        # ==========================================
        license_obj = License.objects.get(project_id=project_id, type="INITIAL")
        self.assertIsNotNone(license_obj.license_number)
        expiry_days = (license_obj.expires_at.date() - timezone.now().date()).days
        # Devrait être environ 180 jours
        self.assertTrue(178 <= expiry_days <= 182)

        # ==========================================
        # CHAPITRE 11 : Suivi et obtention du permis final
        # ==========================================
        # Puisque required_inspections_count = 2, nous devons faire une deuxième inspection
        # Authentifier l'inspecteur
        self.client.force_authenticate(user=self.inspector_user)
        # Passage de l'application à FOLLOWUP_INSPECTIONS (normalement géré par le scheduler/admin)
        app_obj.refresh_from_db()
        app_obj.status = "FOLLOWUP_INSPECTIONS"
        app_obj.save()

        second_inspection = Inspection.objects.create(
            project_id=project_id,
            inspector=self.inspector_user,
            status="PENDING"
        )
        url_report_2 = reverse("inspection-report", kwargs={"pk": second_inspection.id})
        response = self.client.post(url_report_2, report_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Après 2 inspections réussies, statut final
        self.assertEqual(response.data["status"], "FINAL_LICENSE")

        # Vérifier l'édition de la licence finale
        final_license = License.objects.get(project_id=project_id, type="FINAL")
        self.assertIsNotNone(final_license.license_number)

        # Vérification publique (anonyme)
        self.client.force_authenticate(user=None)
        url_public_verify = reverse("license-verify-public", kwargs={"license_number": final_license.license_number})
        response = self.client.get(url_public_verify)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["project_name"], "رحلات الصحراء")

        # ==========================================
        # CHAPITRE FINAL : Nouvel investissement pour utilisateur existant
        # ==========================================
        # Re-authentifier Ahmed
        self.client.force_authenticate(user=ahmed_user)
        # Création d'une autre activité (ex: المطعم السياحي)
        restaurant_service = ServiceType.objects.create(
            name="مطعم سياحي",
            required_inspections_count=1,
            provisional_validity_days=90
        )
        url_project_create = reverse("project-list")
        new_project_data = {
            "project_name": "مطعم النخيل",
            "service_type": restaurant_service.id
        }
        response = self.client.post(url_project_create, new_project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "مطعم النخيل")

        # Vérifier que le nouveau projet et la nouvelle réservation sont associés à Ahmed
        new_project = Project.objects.get(name="مطعم النخيل")
        self.assertEqual(new_project.investor.user, ahmed_user)
        self.assertTrue(NameReservation.objects.filter(name="مطعم النخيل", investor__user=ahmed_user).exists())
