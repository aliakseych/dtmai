import { Suspense } from "react";
import { QuestionBank } from "@/components/practice/QuestionBank";

export default function QuestionBankPage() {
  return (
    <Suspense>
      <QuestionBank />
    </Suspense>
  );
}
