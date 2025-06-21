"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { type Dispatch, type SetStateAction, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
	Form,
	FormControl,
	FormDescription,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { createFromPAT } from "@/services/api";
import DisplayLinks from "./displaylinks";

const formSchema = z.object({
	patstr: z
		.string()
		.startsWith("ghp_", { message: "This is not a valid Github Token." }),
	repolink: z.string().url({ message: "Invalid url" }),
});

interface SignupForm {
	setDeveloperView: Dispatch<SetStateAction<string>>;
	setManagerView: Dispatch<SetStateAction<string>>;
}

function ProfileForm({ setDeveloperView, setManagerView }: SignupForm) {
	const [patsubmitted, setPatSubmitting] = useState(false);

	const form = useForm<z.infer<typeof formSchema>>({
		defaultValues: {
			patstr: "",
		},
		resolver: zodResolver(formSchema),
	});

	async function onSubmit(values: z.infer<typeof formSchema>) {
		setPatSubmitting(false);
		console.log("Submitting PAT");

		const signupresponse = await createFromPAT(values.repolink, values.patstr);
		console.log(signupresponse);
		setPatSubmitting(true);
		setDeveloperView(signupresponse.developerview);
		setManagerView(signupresponse.stakeholderview);
	}

	return (
		<Form {...form}>
			<form className="space-y-8" onSubmit={form.handleSubmit(onSubmit)}>
				<FormField
					control={form.control}
					name="patstr"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Personal Access Token</FormLabel>
							<FormControl>
								<Input
									placeholder="Your token here..."
									type="password"
									{...field}
								/>
							</FormControl>
							<FormDescription>
								Add a PAT with which the referenced repository can be accessed.
							</FormDescription>
							<FormMessage />
						</FormItem>
					)}
				/>

				<FormField
					control={form.control}
					name="repolink"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Github Repository Link</FormLabel>
							<FormControl>
								<Input
									placeholder="Repository link here..."
									type="text"
									{...field}
								/>
							</FormControl>
							<FormDescription>
								The link to the repository accessible with the provided token.
							</FormDescription>
							<FormMessage />
						</FormItem>
					)}
				/>

				{patsubmitted ? (
					<Button disabled>
						<Loader2 className="animate-spin" />
						Setting up. Please wait...
					</Button>
				) : (
					<Button type="submit">Start</Button>
				)}
			</form>
		</Form>
	);
}

export default function SignupMain() {
	const [developerView, setDeveloperView] = useState<string>("");
	const [managerView, setManagerView] = useState<string>("");

	return (
		<div>
			<div className="flex flex-col items-center justify-center min-h-svh">
				{developerView && managerView ? (
					<DisplayLinks
						developerView={developerView}
						managerView={managerView}
					/>
				) : (
					<ProfileForm
						setDeveloperView={setDeveloperView}
						setManagerView={setManagerView}
					/>
				)}
			</div>
		</div>
	);
}
