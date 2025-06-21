"use client";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";

export type CopyTextInputProps = {
	text: string;
};

export function CopyTextInput({ text }: CopyTextInputProps) {
	return (
		<div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
			{text}

			<Button
				onClick={() => navigator.clipboard.writeText(text)}
				variant="outline"
				size="icon"
			>
				<Copy />
			</Button>
		</div>
	);
}

export type LinkListProps = {
	developerView: string;
	managerView: string;
};

export default function DisplayLinks({
	developerView,
	managerView,
}: LinkListProps) {
	return (
		<div className="space-y-3 max-w-md mx-auto">
			<h3>
				These are the links you should share with the developers and managers
				respectively.
			</h3>

			<CopyTextInput text={developerView} />
			<CopyTextInput text={managerView} />
		</div>
	);
}
