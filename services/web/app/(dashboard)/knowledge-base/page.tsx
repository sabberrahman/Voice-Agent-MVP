import { SimpleAdminPage } from "@/components/dashboard/simple-admin-page";

export default function KnowledgeBasePage() {
  return <SimpleAdminPage title="Knowledge Base" description="Future RAG, document upload, FAQ, and source management." endpoint="/admin/knowledge-base" />;
}
