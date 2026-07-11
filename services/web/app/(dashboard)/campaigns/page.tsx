import { SimpleAdminPage } from "@/components/dashboard/simple-admin-page";

export default function CampaignsPage() {
  return <SimpleAdminPage title="Campaigns" description="Outbound campaigns, bulk calling, analytics, and history placeholders." endpoint="/admin/campaigns" />;
}
