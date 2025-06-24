package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.GitRepoInformationConstruct;
import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.SelectionSubmission;
import com.autoback.autoback.persistence.entity.*;
import com.autoback.autoback.persistence.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class GitRepoServiceTest {

    @Mock
    private GitRepoRepository gitRepoRepository;
    @Mock
    private LinkRepository linkRepository;
    @Mock
    private PersonalAccessTokenRepository patRepository;
    @Mock
    private QuestionRepository questionRepository;
    @Mock
    private PersonalAccessToken2GitRepoRepository pat2gitRepository;
    @Mock
    private GitContentRepository gitContentRepository;
    private GitRepoService gitRepoService;
    @BeforeEach
    void setUp() {
        gitRepoService = new GitRepoService(gitRepoRepository, linkRepository, patRepository, pat2gitRepository, questionRepository, gitContentRepository);
    }

    @Test
    void createAccessLinks_WithValidInput_Success() throws NoSuchFieldException, IllegalAccessException {
        // Arrange
        String repoLink = "https://github.com/test/repo";
        String pat = "ghp_validPatToken123";
        PATConstruct patRequest = new PATConstruct(repoLink, pat);

        GitRepo savedRepo = GitRepo.builder().repositoryLink(repoLink).build();
        UUID devLinkUuid = UUID.randomUUID();
        UUID managerLinkUuid = UUID.randomUUID();

        Link devLink = new Link(UUID.randomUUID(),savedRepo.getId(), true);
        Link managerLink = new Link(UUID.randomUUID(),savedRepo.getId(), false);
        // Set UUIDs for the links
        setId(devLink, devLinkUuid);
        setId(managerLink, managerLinkUuid);

        PersonalAccessToken savedPat = new PersonalAccessToken(pat);
        when(gitRepoRepository.findByRepositoryLink(repoLink)).thenReturn(null);
        when(gitRepoRepository.save(any(GitRepo.class))).thenReturn(savedRepo);
        when(linkRepository.save(any(Link.class)))
                .thenReturn(devLink)
                .thenReturn(managerLink);
        when(patRepository.save(any(PersonalAccessToken.class))).thenReturn(savedPat);
        when(pat2gitRepository.save(any(PersonalAccessTokensGitRepository.class))).thenReturn(new PersonalAccessTokensGitRepository(savedPat, savedRepo));

        // Act
        LinkConstruct result = gitRepoService.createAccessLinks(patRequest);

        // Assert
        assertNotNull(result);
        assertEquals(devLinkUuid.toString(), result.developerview());
        assertEquals(managerLinkUuid.toString(), result.stakeholderview());

        verify(gitRepoRepository, times(1)).findByRepositoryLink(repoLink);
        verify(gitRepoRepository, times(1)).save(any(GitRepo.class));
        verify(patRepository, times(1)).save(any(PersonalAccessToken.class));
        verify(pat2gitRepository, times(1)).save(any(PersonalAccessTokensGitRepository.class));
        verify(linkRepository, times(2)).save(any(Link.class));
    }

    @Test
    void createAccessLinks_WithExistingRepo_Success() throws NoSuchFieldException, IllegalAccessException {
        // Arrange
        String repoLink = "https://github.com/test/repo";
        String pat = "ghp_validPatToken123";
        PATConstruct patRequest = new PATConstruct(repoLink, pat);

        GitRepo existingRepo = GitRepo.builder().repositoryLink(repoLink).build();
        UUID devLinkUuid = UUID.randomUUID();
        UUID managerLinkUuid = UUID.randomUUID();

        Link devLink = new Link(UUID.randomUUID(), existingRepo.getId(), true);
        Link managerLink = new Link(UUID.randomUUID(), existingRepo.getId(), false);
        setId(devLink, devLinkUuid);
        setId(managerLink, managerLinkUuid);

        when(gitRepoRepository.findByRepositoryLink(repoLink)).thenReturn(existingRepo);
        when(linkRepository.save(any(Link.class)))
                .thenReturn(devLink)
                .thenReturn(managerLink);

        // Act
        LinkConstruct result = gitRepoService.createAccessLinks(patRequest);

        // Assert
        assertNotNull(result);
        assertEquals(devLinkUuid.toString(), result.developerview());
        assertEquals(managerLinkUuid.toString(), result.stakeholderview());

        verify(gitRepoRepository).findByRepositoryLink(repoLink);
        verify(gitRepoRepository, never()).save(any(GitRepo.class));
        verify(patRepository, never()).save(any(PersonalAccessToken.class));
        verify(linkRepository, times(2)).save(any(Link.class));
    }

    @Test
    void createAccessLinks_WithNullRepoLink_ThrowsException() {
        // Arrange
        PATConstruct patRequest = new PATConstruct(null, "validPat");

        // Act & Assert
        assertThrows(ResponseStatusException.class,
                () -> gitRepoService.createAccessLinks(patRequest));
    }

    @Test
    void createAccessLinks_WithEmptyPAT_ThrowsException() {
        // Arrange
        PATConstruct patRequest = new PATConstruct("https://github.com/test/repo", "");

        // Act & Assert
        assertThrows(ResponseStatusException.class,
                () -> gitRepoService.createAccessLinks(patRequest));
    }

    // Utility method to set private fields for testing
    private void setId(Object object, Object value) throws IllegalAccessException, NoSuchFieldException {
        var field = object.getClass().getDeclaredField("id");
        field.setAccessible(true);
        field.set(object, value);
    }

    @Test
    void getRepositoryByAccessID_Success() throws NoSuchFieldException, IllegalAccessException {
        // Arrange
        UUID validAccessId = UUID.randomUUID();
        Long repoId = 1L;
        Instant createdAt = Instant.now();

        GitRepo validRepo = GitRepo.builder()
                .id(repoId)
                .createdAt(createdAt)
                .questions(new ArrayList<>())
                .summaries(new ArrayList<>())
                .links(new ArrayList<>())
                .contents(new ArrayList<>())
                .repositoryLink("https://github.com/test/repo")
                .build();

        Link validLink = new Link(UUID.randomUUID(),validRepo.getId(), true);
        setId(validLink, validAccessId);

        when(linkRepository.findById(validAccessId)).thenReturn(Optional.of(validLink));
        when(gitRepoRepository.findById(validLink.getGitRepositoryId())).thenReturn(Optional.of(validRepo));

        // Act
        GitRepoInformationConstruct result = gitRepoService.getRepositoryByAccessID(validAccessId);

        // Assert
        assertNotNull(result);
        assertEquals(validRepo.getRepositoryLink(), result.repoLink());
        assertTrue(result.isMaintainer());
        assertEquals(createdAt,validRepo.getCreatedAt());
        assertEquals(validRepo.getCreatedAt(), result.createdAt());
        assertTrue(result.questions().isEmpty());
        assertTrue(result.summaries().isEmpty());
        assertTrue(result.contents().isEmpty());

        verify(linkRepository).findById(validAccessId);
        verify(gitRepoRepository).findById(validLink.getGitRepositoryId());
    }

    @Test
    void getRepositoryByAccessID_InvalidAccessId_ThrowsForbidden() {
        // Arrange
        UUID invalidAccessId = UUID.randomUUID();
        when(linkRepository.findById(invalidAccessId)).thenReturn(Optional.empty());

        // Act & Assert
        ResponseStatusException exception = assertThrows(ResponseStatusException.class,
                () -> gitRepoService.getRepositoryByAccessID(invalidAccessId));

        assertEquals(HttpStatus.FORBIDDEN, exception.getStatusCode());
        assertEquals("link is not a valid access id", exception.getReason());

        verify(linkRepository).findById(invalidAccessId);
        verify(gitRepoRepository, never()).findById(any());
    }

    @Test
    void getRepositoryByAccessID_RepoNotFound_ThrowsNotFound() throws NoSuchFieldException, IllegalAccessException {
        // Arrange
        UUID validAccessId = UUID.randomUUID();
        Long repoId = 1L;

        GitRepo validRepo = GitRepo.builder().repositoryLink("https://github.com/test/repo").id(repoId).build();

        Link validLink = new Link(UUID.randomUUID(), validRepo.getId(), true);
        setId(validLink, validAccessId);

        when(linkRepository.findById(validAccessId)).thenReturn(Optional.of(validLink));
        when(gitRepoRepository.findById(validLink.getGitRepositoryId())).thenReturn(Optional.empty());

        // Act & Assert
        ResponseStatusException exception = assertThrows(ResponseStatusException.class,
                () -> gitRepoService.getRepositoryByAccessID(validAccessId));

        assertEquals(HttpStatus.NOT_FOUND, exception.getStatusCode());
        assertEquals("link does not point to a repository", exception.getReason());

        verify(linkRepository).findById(validAccessId);
        verify(gitRepoRepository).findById(validLink.getGitRepositoryId());
    }
    @Test
    void createCommitSelection_WithValidAccessId_Success() {
        // Arrange
        UUID validAccessId = UUID.randomUUID();
        Content c1 = Content.builder().id("asdsda").build();
        Content c2 = Content.builder().id("ladsad").build();
        SelectionSubmission selection = new SelectionSubmission(Set.of(c1.getId(), c2.getId()));
        GitRepo validRepo = GitRepo.builder().repositoryLink("https://github.com/test/repo").build();
        Link validLink = new Link(UUID.randomUUID(), validRepo.getId(), true);
        validLink.setGitRepositoryId(42L);

        when(linkRepository.findById(validAccessId)).thenReturn(Optional.of(validLink));
        when(gitContentRepository.findDistinctByCreatedAtAfterAndGitRepositoryId(any(Instant.class),eq(validLink.getGitRepositoryId()))).thenReturn(Set.of(c1, c2));

        // Act
        assertDoesNotThrow(() -> gitRepoService.createCommitSelection(validAccessId, selection));

        // Assert
        verify(linkRepository).findById(validAccessId);
        verify(gitContentRepository).findDistinctByCreatedAtAfterAndGitRepositoryId(any(Instant.class),eq(validLink.getGitRepositoryId()));
        verify(gitContentRepository,times(2)).save(any());
        verifyNoMoreInteractions(linkRepository, gitContentRepository);
    }

    @Test
    void createCommitSelection_WithInvalidAccessId_ThrowsForbidden() {
        // Arrange
        UUID invalidAccessId = UUID.randomUUID();
        SelectionSubmission selection = new SelectionSubmission(Set.of("asdsda", "ladsad"));

        when(linkRepository.findById(invalidAccessId)).thenReturn(Optional.empty());

        // Act & Assert
        ResponseStatusException exception = assertThrows(ResponseStatusException.class,
                () -> gitRepoService.createCommitSelection(invalidAccessId, selection));

        assertEquals(HttpStatus.FORBIDDEN, exception.getStatusCode());
        assertEquals("link is not a valid access id", exception.getReason());
        verify(linkRepository).findById(invalidAccessId);
    }

    @Test
    void createQuestion_WithInvalidAccessId_ThrowsForbidden() {
        // Arrange
        UUID invalidAccessId = UUID.randomUUID();
        String question = "Why is this code structured this way?";

        when(linkRepository.findById(invalidAccessId)).thenReturn(Optional.empty());

        // Act & Assert
        ResponseStatusException exception = assertThrows(ResponseStatusException.class,
                () -> gitRepoService.createQuestion(invalidAccessId, question));

        assertEquals(HttpStatus.FORBIDDEN, exception.getStatusCode());
        assertEquals("link is not a valid access id", exception.getReason());

        verify(linkRepository).findById(invalidAccessId);
        verify(questionRepository, never()).save(any(Question.class));
    }
}
