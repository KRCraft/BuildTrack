"use client";
import { useParams } from "next/navigation";
import { ExpensesPage } from "@/components/expenses-page";
export default function ProjectExpensesPage(){const {id}=useParams<{id:string}>();return <ExpensesPage projectId={id}/>}
